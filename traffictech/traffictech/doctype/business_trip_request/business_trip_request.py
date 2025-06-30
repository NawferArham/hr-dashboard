# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class BusinessTripRequest(Document):
	@frappe.whitelist()
	def upload_ocr_document(self, file_url):
		exp_entry = frappe.new_doc("Petty Cash Entry")
		ocr_data = exp_entry.ocr_document_file(file_url)
		entry_name, entry = create_update_entry(file_url, ocr_data, entry=self.petty_cash_entry, employee=self.employee)
		if not entry_name:
			return

		self.db_set("petty_cash_entry", entry_name)
		for datum in entry:
			self.append("employee_expenses", {
				"supplier": datum.get("supplier"),
				"supplier_invoice_no": datum.get("supplier_invoice_no"),
				"amount": datum.get("grand_total"),
				"date": datum.get("supplier_invoice_date"),
				"attachment": file_url,
			})
		self.save()

	@frappe.whitelist()
	def fetch_user_details(self):
		if not self.employee:
			employee = frappe.get_value(
				"Employee", 
				{"user_id": frappe.session.user}, 
				["name", "department", "designation", "employee_name", "user_id"],
				as_dict=1
			)
			if not employee:
				return
			
			self.db_set("employee", employee.get("name"))
			self.db_set("department", employee.get("department"))
			self.db_set("ttile", employee.get("designation"))
			self.db_set("employee_name", employee.get("employee_name"))
			self.db_set("user_id", frappe.session.user)

	@frappe.whitelist()
	def get_invoice_items(self, invoice):
		items = frappe.db.get_all(
			"Petty Cash Entry Item", 
			{"parent": self.petty_cash_entry, "supplier_invoice_no": invoice}, 
			["*"]
		)

		return items


def create_update_entry(file_url, outputs, entry=None, employee=None):
	new_entry = frappe.new_doc("Petty Cash Entry")
	new_entry.employee = employee
	if entry:
		new_entry = frappe.get_doc("Petty Cash Entry", entry)

	for output in outputs:
		output = frappe.parse_json(output)
		
		new_entry.append("bills", {
			"attachment": file_url,
			"supplier": output.supplier,
			"supplier_invoice_date": output.date,
			"supplier_invoice_no": output.supplier_invoice_no,
			"currency": output.currency,
			"tax_and_charges": output.tax,
			"discount_amount": output.discount,
			"document_type": output.document_type,
			"category": output.category,
			"json_data": json.dumps(output)
		})

		for row in output.get("items"):
			add_child = new_entry.append("items", {})
			add_child.description = row.get("description")
			add_child.qty = row.get("qty")
			add_child.rate = row.get("rate")
			add_child.supplier_invoice_no = output.supplier_invoice_no

		# new_entry.insert()
	new_entry.validate()
	new_entry.save(ignore_permissions=True)
	return new_entry.name, new_entry.bills[-len(outputs):]

