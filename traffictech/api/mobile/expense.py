# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def get_all_pce(from_date=None, to_date=None, status=None):
	try:
		filters={"owner": frappe.session.user}
		if from_date:
			filters["posting_date"] = [">=", from_date]
		if to_date:
			filters["posting_date"] = ["<=", to_date]
		if status:
			if status != "All":
				filters["status"] = status

		expenses = frappe.db.get_all("Petty Cash Entry", fields=["name"], filters=filters)
		for row in expenses:
			row.update(get_pce_details(row.name, from_api=True))

		return {
			"success": True,
			"expenses": expenses
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get Expenses Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_pce_details(id, from_api=False):
	try:
		entry = frappe.db.get_value("Petty Cash Entry", id, 
			[
				"posting_date", "status", "project", "reason", "employee", 
				"employee_name", "grand_total", "tax_and_charges", "discount_amount", 
				"rejection_reason"
			],
			as_dict=True
		)
		if not entry and not from_api:
			return {"success": False, "error": "Entry not found"}

		entry_bills = []
		bills = frappe.db.get_all(
			"Petty Cash Entry Bill",
			filters={"parent": id},
			fields="json_data"
		)

		for bill in bills:
			entry_bills.append(frappe.parse_json(bill["json_data"]))

		entry["bills"] = entry_bills

		if from_api:
			return entry

		return {
			"success": True,
			"entry": entry
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get Petty Cash Entry Details Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_pce(**kwargs):
	try:
		entry = frappe.new_doc("Petty Cash Entry")

		if kwargs.get("project_based"):
			if not kwargs.get("project"):
		  		return {"success": False, "error": "Project is required for project-based entries"}
		
		entry.project = kwargs.get("project")
		entry.currency = kwargs.get("currency")
		entry.save()

		for bill in kwargs.get("bills", []):
			filedata = bill.get("filedata")
			filetype = bill.get("filetype")

			if filedata and filetype:
				_file = frappe.get_doc(
					{
						"doctype": "File",
						"file_name": f"{frappe.generate_hash('', 5)}.{filetype}",
						"attached_to_doctype": "Petty Cash Entry",
						"attached_to_name": entry.name,
						"is_private": 1,
						"content": filedata,
						"decode": True,
					}
				)
				_file.save(ignore_permissions=True)

				outputs = entry.ocr_document_file(_file.file_url)

				if not outputs:
					continue

				for output in outputs:
					entry.append("bills", {
						"attachment": _file.file_url,
						'json_data': frappe.as_json(output),
						'document_type': output.get("document_type"),
						'supplier': output.get("supplier"),
						'supplier_invoice_no': output.get("supplier_invoice_no"),
						'supplier_invoice_date': output.get("date"),
						'currency': output.get("currency"),
						'category': output.get("category"),
						'total_qty': output.get("total_quantity"),
						'total': output.get("subtotal"),
						'tax_and_charges': output.get("tax"),
						'discount_amount': output.get("discount"),
						'grand_total': output.get("grand_total")
					})

					for item in output.get("items"):
						entry.append("items", {
							"description": item.get("description"),
							"qty": item.get("qty"),
							"rate": item.get("rate"),
							"amount": item.get("amount"),
							"supplier_invoice_no": output.get("supplier_invoice_no")
						})
		entry.save()

		return {"success": True, "message": "Petty Cash Entry created successfully", "name": entry.name}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Create Petty Cash Entry Error")
		return {"success": False, "error": str(e)}



@frappe.whitelist()
def update_pce(**kwargs):
	try:
		entry = frappe.get_doc("Petty Cash Entry", kwargs.get("id"))
		if not entry:
			return {"success": False, "error": "Petty Cash Entry not found"}
		
		entry.project = kwargs.get("project")
		entry.currency = kwargs.get("currency")

		for rm in kwargs.get("remove_bills", []):
			if rm.get("invoice_no"):
				for bill_ in entry.bills:
					if bill_.supplier_invoice_no == rm["invoice_no"]:
						entry.bills.remove(bill_)
						break

		entry.save()

		for bill in kwargs.get("new_bills", []):
			filedata = bill.get("filedata")
			filetype = bill.get("filetype")

			if filedata and filetype:
				_file = frappe.get_doc(
					{
						"doctype": "File",
						"file_name": f"{frappe.generate_hash('', 5)}.{filetype}",
						"attached_to_doctype": "Petty Cash Entry",
						"attached_to_name": entry.name,
						"is_private": 1,
						"content": filedata,
						"decode": True,
					}
				)
				_file.save(ignore_permissions=True)

				outputs = entry.ocr_document_file(_file.file_url)

				if not outputs:
					continue

				for output in outputs:
					entry.append("bills", {
						"attachment": _file.file_url,
						'json_data': frappe.as_json(output),
						'document_type': output.get("document_type"),
						'supplier': output.get("supplier"),
						'supplier_invoice_no': output.get("supplier_invoice_no"),
						'supplier_invoice_date': output.get("date"),
						'currency': output.get("currency"),
						'category': output.get("category"),
						'total_qty': output.get("total_quantity"),
						'total': output.get("subtotal"),
						'tax_and_charges': output.get("tax"),
						'discount_amount': output.get("discount"),
						'grand_total': output.get("grand_total")
					})

					for item in output.get("items"):
						entry.append("items", {
							"description": item.get("description"),
							"qty": item.get("qty"),
							"rate": item.get("rate"),
							"amount": item.get("amount"),
							"supplier_invoice_no": output.get("supplier_invoice_no")
						})
		entry.save()

		return {"success": True, "message": "Petty Cash Entry Updated successfully", "name": entry.name}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Update Petty Cash Entry Error")
		return {"success": False, "error": str(e)}