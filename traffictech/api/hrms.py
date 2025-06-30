
import json

import frappe
from frappe.integrations.utils import create_request_log
from erpnext.setup.doctype.designation.test_designation import create_designation
# from frappe.utils import flt, today

@frappe.whitelist(methods=["POST"])
def make_employee():
	try:
		data = json.loads(frappe.request.data)
		flag = 0
		employee_number = data.get("employee_number")
		department = data.get("department")
		designation = data.get("designation")
		employee_id = frappe.db.get_value("Employee", {"employee_number": employee_number}, "name")
		if employee_id:
			flag = 1
			employee = frappe.get_doc("Employee", employee_id)
		else:
			employee = frappe.new_doc("Employee")

		if department:
			department_id = get_department(department)
			employee.set("department", department_id)
		
		if designation:
			if not has_designation(designation):
				create_designation(designation_name=designation)

		for field in data:
			if field in ["department"]:
				continue
				
			if data.get(field) and employee.meta.has_field(field):
				employee.set(field, data.get(field))

		employee.save(ignore_permissions=True)
		
		return {
			"success": True, 
			"message": "Employee Updated" if flag else "Employee Created",
		}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(str(frappe.get_traceback()), "Create Employee")
		create_request_log(
			data=json.loads(frappe.request.data),
			request_description = "Create Project",
			service_name="Traffic Tech",
			request_headers=frappe.request.headers,
			error=str(e),
			status="Failed"
		)
		return {"success": False, "error": str(e)}


def has_designation(designation):
	if frappe.db.exists("Designation", designation):
		return True

def get_department(department):
	department_id = frappe.db.get_value("Department", {"department_name": department}, "name")
	if department_id:
		return department_id
	doc = frappe.get_doc(
		{
			"doctype": "Department",
			"is_group": 0,
			# "parent_department": "",
			"department_name": department,
			"name": department,
			"company": frappe.defaults.get_defaults().company,
		}
	).insert(ignore_permissions=True)

	return doc.name