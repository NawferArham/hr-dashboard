# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from traffictech.api.mobile.auth import get_employee_info
from frappe.utils import strip_html


@frappe.whitelist()
def get_user_profile():
	try:
		return get_employee_info()
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get User Profile Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_employee_list():
	try:
		employees = frappe.db.get_list(
			"Employee",
			fields=["name", "employee_name", "department", "designation"],
			filters={"status": "Active"},
			order_by="employee_name"
		)
		return {
			"success": True,
			"employees": employees
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get Employee List Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_notifications():
	try:
		notifications = frappe.get_all(
			"Notification Log",
			fields=["name", "subject", "email_content", "creation", "from_user", "type"],
			filters={"read": 0, "for_user": frappe.session.user},
			order_by="creation desc"
		)

		for n in notifications:
			if n.get("subject"):
				n["subject"] = strip_html(n["subject"])
			if n.get("email_content"):
				n["email_content"] = strip_html(n["email_content"])
		
		return {
			"success": True,
			"notifications": notifications
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get Notifications Error")
		return {"success": False, "error": str(e)}

	
@frappe.whitelist()
def mark_notification_as_read(notifications):
	try:
		frappe.db.set_value("Notification Log", {"name": ["in", notifications]}, "read", 1)
		return {
			"success": True,
			"message": "Notification marked as read"
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Mark Notification as Read Error")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_email_queue():
	try:
		em = frappe.qb.DocType("Email Queue")
		em_r = frappe.qb.DocType("Email Queue Recipient")

		email_queue = (
			frappe.qb.from_(em)
			.inner_join(em_r).on(em.name == em_r.parent)
			.select(em.name, em.message, em.status, em.creation)
			.where(
				(em.status.isin(["Sending"]))
				& (em_r.recipient == frappe.session.user)
			)
			.orderby(em.creation, order=frappe.qb.desc)
			.run(as_dict=True)
		)

		for eq in email_queue:
			if eq.get("message"):
				eq["message"] = strip_html(eq["message"])

		return {
			"success": True,
			"email_queue": email_queue
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get Email Queue Error")
		return {"success": False, "error": str(e)}