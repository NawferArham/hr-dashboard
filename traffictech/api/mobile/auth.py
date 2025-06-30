# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from traffictech.api.portal.auth import authenticate, logout
from traffictech.api.portal.utils import get_current_employee_info


@frappe.whitelist()
def get_employee_info():
	try:
		current_user = frappe.session.user
		employee_info = get_current_employee_info(current_user)
		if not employee_info.get("data"):
			return  {
				"success": False,
				"error": "Employee not found"
			}
		
		return {
			"success": True,
			"employee_info": employee_info.get("data")
		}
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()), title="Mobile API: Get Employee Info Error")
		return {"success": False, "error": str(e)}