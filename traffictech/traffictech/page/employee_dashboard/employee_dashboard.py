import frappe

@frappe.whitelist()
def get_todos():
	todos = frappe.db.get_list("ToDo", 
		{"allocated_to": frappe.session.user, "status": "Open"}, 
		["description", "date", "name"], 
		limit=6, 
		order_by="date asc"
	) 

	return todos


@frappe.whitelist()
def get_emp_details():
	emp = frappe.db.get_value("Employee", 
		{"user_id": frappe.session.user}, 
		["name", "employee_name", "image", "department", "reports_to", "date_of_joining"],
		as_dict=1
	)

	if emp.get("reports_to"):
		emp["reports_to"] = frappe.db.get_value("Employee", emp.get("reports_to"), "employee_name")

	return emp