# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import os
import json
from frappe.utils import flt, today
from frappe.integrations.utils import get_json
from frappe import _
from traffictech.traffictech.doctype.expense_entry.expense_entry import (
	convert_to_image,
	pil_to_high_res,
	auto_crop_image,
	pil_to_grayscale,
	pil_to_invert,
	correct_image_orientation,
	convert_to_base64,
	AI_OCR,
	validate_output
)
from frappe.utils.xlsxutils import make_xlsx
import io
import zipfile
from frappe.utils import get_files_path


class PettyCashEntry(Document):
	# def before_insert(self):
	# 	if not self.employee:
	# 		self.employee_name = frappe.db.get_value("Employee", frappe.session.user, "employee_name")

	def before_save(self):
		self.validate_and_remove_items()

	def validate(self):
		self.update_bills()
		self.update_business_trip()
		self.link_file_reference()

	def on_submit(self):
		if self.status != "Approved":
			frappe.throw("Approve the Bills First!")

	def update_bills(self):
		status_wise = {}
		self.grand_total = 0
		self.tax_and_charges = 0
		self.discount_amount = 0

		for row in self.bills:
			self.calculate_total(row)
			self.check_category(row)
			self.format_json_data(row)
			self.calculate_conversion_total(row)
			self.validate_supplier_invoice(row)

			status_wise.setdefault(row.status, 0)
			status_wise[row.status] += 1

			self.grand_total += flt(row.grand_total)
			self.tax_and_charges += flt(row.tax_and_charges)
			self.discount_amount += flt(row.discount_amount)
			row.item_status = self.get_item_status(row.supplier_invoice_no)
		
		status = "Pending"
		if status_wise.get("Approve", 0) == len(self.bills):
			status = "Approved"
		if status_wise.get("Reject", 0) == len(self.bills):
			status = "Rejected"
		if status_wise.get("Approve") and status_wise.get("Approve") < len(self.bills):
			status = "Partial Approved"
		# if status_wise.get("Resubmit", 0) > 0:
		# 	status = "Resubmitted"
		self.status = status

	@frappe.whitelist()
	def update_item_status(self, items, invoice):
		items = frappe.parse_json(items)
		for item in items:
			for row in self.items:
				if row.supplier_invoice_no == invoice and item.get("description") == row.description and item.get("qty") == row.qty:
					row.status = item.get("status")


	def get_item_status(self, invoice):
		status_wise = {}
		items_len = 0
		for row in self.items:
			if row.supplier_invoice_no == invoice:
				status_wise.setdefault(row.status, 0)
				status_wise[row.status] += 1
				items_len += 1
			
		status = "Pending"
		if status_wise.get("Approve", 0) == items_len:
			status = "Approved"
		if status_wise.get("Reject", 0) == items_len:
			status = "Rejected"
		if status_wise.get("Approve") and status_wise.get("Approve") < items_len:
			status = "Partial Approved"

		return status

	def format_json_data(self, row):
		if row.json_data:
			data = json.loads(row.json_data)
			row.json_data = get_json(data)

	def link_file_reference(self):
		for row in self.bills:
			if row.attachment:
				files = frappe.db.get_value("File", {
					"file_url": row.attachment
				}, ["attached_to_name", "name"], as_dict=1)
				if files and not files.attached_to_name:
					frappe.db.set_value("File", files.name, {
						"attached_to_doctype": self.doctype,
						"attached_to_name": self.name,
						"attached_to_field": "attachment"
					})


	def calculate_total(self, row):
		row.total_qty = 0
		row.total = 0
		for d in self.items:
			if d.supplier_invoice_no == row.supplier_invoice_no:
				d.amount = flt(d.qty) * flt(d.rate)
				row.total_qty += flt(d.qty)
				row.total += d.amount

		row.net_total = flt(row.total) - flt(row.discount_amount)
		row.grand_total = flt(row.net_total) + flt(row.tax_and_charges)
	
	def calculate_conversion_total(self, row):
		if not self.conversion_rate:
			self.conversion_rate = 1

		total_base_amount = 0
		for d in self.items:
			if d.supplier_invoice_no == row.supplier_invoice_no: 
				d.base_rate = flt(d.rate) * flt(self.conversion_rate, 9)
				d.base_amount = flt(d.qty) * flt(d.base_rate)
				total_base_amount += flt(d.base_amount)
		
		row.base_total = total_base_amount

		row.base_discount_amount = flt(row.discount_amount) * flt(self.conversion_rate, 9)

		row.base_net_total = flt(row.base_total) - flt(row.base_discount_amount)

		row.base_tax_and_charges = flt(row.tax_and_charges) * flt(self.conversion_rate, 9)

		row.base_grand_total = flt(row.base_net_total) + flt(row.base_tax_and_charges)

	@frappe.whitelist()
	def check_category(self, row):
		if row.category:
			alert = frappe.db.get_value("Expense Category", row.category, "alert_category")
			if alert:
				frappe.msgprint(
					_("This Petty Cash Entry belongs to the '{0}' category. Please verify the document before submitting.").format(row.category)
				)

	def validate_supplier_invoice(self, row):
		if row.supplier_invoice_no:
			ee = frappe.db.sql(
				"""select idx, parent from `tabPetty Cash Entry Bill`
				where
					supplier_invoice_no = %(supplier_invoice_no)s
					and supplier = %(supplier)s
					and name != %(name)s
					and docstatus < 2
					and status = 'Approve'""",
				{
					"supplier_invoice_no": row.supplier_invoice_no,
					"supplier": row.supplier,
					"name": row.name,
				},
			)

			if ee:
				ee = ee[0]

				frappe.throw(
					_("Supplier Invoice No exists in Petty Cash Entry {0} at row {1}").format(
						ee[1], ee[0]
					)
				)

	@frappe.whitelist()
	def ocr_document_file(self, file_url):
		file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
		file_is_private = file_url.startswith("/private/files/")
		FILE_PATH = frappe.utils.get_files_path(file_name, is_private=file_is_private)

		if not os.path.exists(FILE_PATH):
			frappe.throw("File does not exist")

		images = convert_to_image(FILE_PATH)

		image_preprocess = [
			pil_to_high_res,
			auto_crop_image,
			pil_to_grayscale,
			pil_to_invert,
			correct_image_orientation,
			convert_to_base64,
		]

		outputs = []
		for image in images:
			for pre_process in image_preprocess:
				try:
					image = pre_process(image)
				except Exception as e:
					frappe.log_error("Error OCR Single Page", str(e))
					continue

			try:
				output = AI_OCR(image)
				validate_output(output)
				self.validate_currency(output)
				outputs.append(output)
			except Exception as e:
				frappe.log_error("Error OCR Single Page", str(e))
				continue
		return outputs

	@frappe.whitelist()
	def scan_documents(self, files):
		self.message_for_scanner = []
		outputs = []

		for file in files:
			for output in self.ocr_document_file(file):
				output["file_url"] = file
				if frappe.db.get_value(
					"Petty Cash Entry Bill", 
					{
						"supplier_invoice_no": output["supplier_invoice_no"],
						"supplier": output["supplier"],
						"docstatus": ["<", 2],
					}
				):
					self.message_for_scanner.append(output["supplier_invoice_no"])
				else:
					outputs.append(output)

		return {"outputs": outputs, "message": self.message_for_scanner}

	@frappe.whitelist()
	def get_invoice_items(self, invoice):
		items = []
		for row in self.items:
			if row.supplier_invoice_no == invoice:
				items.append(row)
		
		return items
	
	def update_business_trip(self):
		status = "Pending"
		if self.get("workflow_state") and "Rejected" in self.get("workflow_state"):
			status = "Rejected"
		if self.docstatus == 1:
			status = "Approved"
		
		frappe.db.set_value(
			"Business Trip Request", 
			{"petty_cash_entry": self.name}, 
			"status_of_entry", 
			status
		)

	def validate_currency(self, output):
		if self.is_new():
			return
		
		if output.get("currency") and self.currency != output["currency"]:
			frappe.throw(f"Cannot attach adocument which is in another Currency, Only {self.currency} is acceptable for this Entry")

	@frappe.whitelist()
	def email_to_initiator(self):
		"""Send an email to the initiator with the given comment and document link."""
		doc_link = frappe.utils.get_url_to_form("Petty Cash Entry", self.name)

		comments = []
		for row in self.bills:
			if row.comments:
				comments.append(f"{row.supplier_invoice_no}: {row.comments}")

		if not comments:
			frappe.throw("No Comments to revise!")

		subject = "New Revise Comment from Petty Cash"
		message = f"""
			<p>Hello,</p>
			<p>You have a new comment on the <a href="{doc_link}">Petty Cash Entry: {self.name}</a>.</p>
			<p><strong>Comments:</strong> {", ".join(comments)}</p>
			<p>Thank You</p>
		"""

		try:
			frappe.sendmail(
				recipients=[self.owner],
				subject=subject,
				message=message
			)
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Email to Initiator Failed")
			raise e

	def validate_and_remove_items(self):
		bills = []
		rejected_bills = []
		for inv in self.bills:
			if inv.supplier_invoice_no not in bills:
				bills.append(inv.supplier_invoice_no)

			if inv.status == "Reject" or inv.item_status == "Rejected":
				rejected_bills.append(inv)

		self.rejected_bills = []
		for rj in rejected_bills:
			bills.remove(rj.supplier_invoice_no)

			self.bills.remove(rj)
			rj = rj.as_dict()
			rj["idx"] = ""
			rj["name"] = ""
			self.append("rejected_bills", rj)
		
		if not self.bills:
			self.items = []
		for row in self.items:
			if (row.supplier_invoice_no not in bills):
				self.items.remove(row)

@frappe.whitelist()
def download_report(pce):
	doc = frappe.get_doc("Petty Cash Entry", pce)

	if doc.downloaded:
		frappe.msgprint("Report already Downloaded")

	frappe.response["filename"] = f"{pce}-export.zip"
	frappe.response["filecontent"] = generate_report([pce])
	frappe.response["type"] = "binary"

	doc.db_set("downloaded", 1)


@frappe.whitelist()
def download_report_bulkly(pce):
	if isinstance(pce, str):
		pce = json.loads(pce)
	if not pce:
		frappe.throw(_("No Entry selected."))

	data = generate_report(pce)

	frappe.response["filename"] = f"{today()}-pce-report.zip"
	frappe.response["filecontent"] = data
	frappe.response["type"] = "binary"


def generate_report(bills):
	zip_buffer = io.BytesIO()
	all_data = []

	columns = [
		"Transaction No", "Supplier Code", "PSD Date", "PSD Reason",
		"LiqAccCode", "Currency", "Amount", "Requester"
	]

	with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
		for pce in bills:
			doc = frappe.get_doc("Petty Cash Entry", pce)

			if doc.status != "Approved":
				continue

			all_data.append([
				doc.name,
				"CR000001",
				doc.posting_date,
				doc.reason,
				"FA-000",
				doc.currency,
				doc.grand_total,
				doc.owner
			])

			for idx, bill in enumerate(doc.bills):
				idx += 1
				# Add attachments
				if bill.attachment:
					file_doc = frappe.get_doc("File", {"file_url": bill.attachment})
					file_path = get_files_path(file_doc.file_name, is_private=file_doc.is_private)

					with open(file_path, "rb") as f:
						file_content = f.read()
						filename_in_zip = f"{pce}-{idx}"
						zf.writestr(filename_in_zip, file_content)

		# After collecting all bill data, create one Excel
		xlsx_data = [columns] + all_data
		xlsx_file = make_xlsx(xlsx_data, f"All Bills Report-{today()}")

		# Add single Excel to zip
		zf.writestr(f"{today()}.xlsx", xlsx_file.getvalue())

	zip_buffer.seek(0)
	return zip_buffer.getvalue()