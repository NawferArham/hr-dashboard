# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import base64
import json
import frappe
from frappe.utils.password import get_decrypted_password
from traffictech.api.portal.utils import get_current_employee_info


@frappe.whitelist(allow_guest=True)
def authenticate():
	try:
		data = json.loads(frappe.request.data)
		username = data.get("username")
		password = data.get("password")
		try:
			login_manager = frappe.auth.LoginManager()
			login_manager.authenticate(user=username, pwd=password)
		except Exception:
			frappe.local.response["status_code"] = 400
			return {"success": False, "message": "Invalid username or password"}

		login_manager.post_login()
		api_key, api_secret = generate_keys(username)
		employee_details = get_current_employee_info(username)
		return {
			"success": True,
			"message": "Logged In Succesfully",
			"api_key": api_key,
			"api_secret": api_secret,
			"emp_info": employee_details
		}
	except Exception as e:
		frappe.log_error(str(e), "Auth Error")
		return {"success": False, "error": str(e)}


def generate_keys(user):
	api_secret = get_decrypted_password("User", user, "api_secret", raise_exception=False)
	if not api_secret:
		user_details = frappe.get_doc("User", user)
		api_secret = frappe.generate_hash(length=15)
		# if api key is not set generate api key
		if not user_details.api_key:
			api_key = frappe.generate_hash(length=15)
			user_details.api_key = api_key
		user_details.api_secret = api_secret
		user_details.save(ignore_permissions=True)
	else:
		api_key = frappe.db.get_value("User", user, "api_key")

	return api_key, api_secret


@frappe.whitelist()
def logout():
	frappe.local.login_manager.logout()
	frappe.db.commit()