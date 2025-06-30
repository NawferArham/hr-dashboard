
import json

import frappe
from frappe.integrations.utils import create_request_log

@frappe.whitelist(methods=["POST"])
def make_project():
	try:
		data = json.loads(frappe.request.data)
		flag = 0
		project_id = data.get("project_id")
		project_no = frappe.db.get_value("Project", {"name": project_id}, "name")
		if project_no:
			flag = 1
			project = frappe.get_doc("Project", project_no)
		else:
			project = frappe.new_doc("Project")
			project.name = project_id
			project.set("name", project_id)

		customer = data.get("customer")

		if customer:
			customer_id = get_customer(customer)
			project.set("customer", customer_id)

		for field in data:
			if field in ["customer", "project_id"]:
				continue
				
			if data.get(field) and project.meta.has_field(field):
				project.set(field, data.get(field))

		project.save(ignore_permissions=True)
		if project_id != project.name:
			frappe.rename_doc("Project", project.name, project_id)

		return {
			"success": True, 
			"message": "Project Updated" if flag else "Project Created",
		}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(str(frappe.get_traceback()), "Create Project")
		create_request_log(
			data=json.loads(frappe.request.data),
			request_description = "Create Project",
			service_name="Traffic Tech",
			request_headers=frappe.request.headers,
			error=str(e),
			status="Failed"
		)
		return {"success": False, "error": str(e)}


def get_customer(customer):
	customer_id = frappe.db.get_value("Customer", {"name": customer}, "name")
	if customer_id:
		return customer_id
	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer,
			"customer_type": "Individual",
			"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group"),
		}
	).insert(ignore_permissions=True)

	return doc.name