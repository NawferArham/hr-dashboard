# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import json
import frappe
import base64
from frappe.utils import now, today, add_days, date_diff, getdate
from traffictech.api.portal.utils import (
    is_recognized, save_base64_to_file, 
	get_attendance_for_calendar, get_holidays_for_calendar
)

    
@frappe.whitelist()
def checkin():
	try:
		data = json.loads(frappe.request.data)
		doc = frappe.new_doc("Employee Checkin")
		doc.employee = data.get("employee")
		doc.log_type = data.get("log_type")	
		doc.device_id = data.get("device_id")	
		doc.time = data.get("timestamp") or now()
		doc.reason = data.get("reason")
		doc.insert()

		return {
			"success": True,
			"message": "Checkin Marked Succesfully",
			"data": doc.name
		}
				
	except Exception as e:
		frappe.log_error(str(e), "Error HRMS Checkin")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_employee_image():
	try:
		data = json.loads(frappe.request.data)
		employee = data.get("employee")
		file_url = frappe.db.get_value('Employee', employee, "image")
		if not file_url:
			return {"success": False, "error": "Employee image missing"}

		file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
		file_is_private = file_url.startswith("/private/files/")
		full_path = frappe.utils.get_files_path(file_name, is_private=file_is_private)
		
		file = open(full_path, 'rb')
		try:
			file_content = file.read()
		finally:
			file.close()

		base64_image = base64.b64encode(file_content).decode('utf-8')
		
		return {
			"success": True,
			"data": base64_image
		}
				
	except Exception as e:
		frappe.log_error(str(e), "Error Get Employee Image")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_qr_code():
	data = json.loads(frappe.request.data)
	scanned_code = data.get("scanned_code")
	if not scanned_code:
		return {"success": False, "message": "Invalid QR code!"}

	current_qr = frappe.db.get_value("Office QRCode", "Office QRCode", "qrcode_data")

	if scanned_code == current_qr:
		return {"success": True, "message": "QR code is valid!",  "data":[scanned_code, current_qr]}
	else:
		return {"success": False, "message": "Invalid QR code!", "data":[scanned_code, current_qr]}


@frappe.whitelist()
def get_recent_log():
	data = json.loads(frappe.request.data)
	employee = data.get("employee")

	if not employee:
		return {"success": False, "message": "Employee is missing",}

	log = frappe.db.get_all("Employee Checkin", {
		"employee": employee
	}, ["log_type", "time", "device_id"], order_by="time desc", limit=15)

	current_status = frappe.db.get_value(
		"Employee Checkin",
		{
			"employee": employee,
			"time": ["between", [f"{today()} 00:00:00", f"{today()} 23:59:59"]]
		},
		"log_type",
		order_by="time desc"
	)

	return {"success": True, "current_status": current_status, "logs": log}


@frappe.whitelist()
def get_employee_documents():
	try:
		data = json.loads(frappe.request.data)
		employee = data.get("employee")
		fieldname = data.get("fieldname")
		file_url = frappe.db.get_value('Employee', employee, fieldname)
		if not file_url:
			return {"success": False, "error": "No Attachment Found"}

		file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
		file_is_private = file_url.startswith("/private/files/")
		full_path = frappe.utils.get_files_path(file_name, is_private=file_is_private)
		
		file = open(full_path, 'rb')
		try:
			file_content = file.read()
		finally:
			file.close()

		base64_image = base64.b64encode(file_content).decode('utf-8')
		
		return {
			"success": True,
			"data": base64_image
		}
				
	except Exception as e:
		frappe.log_error(str(e), "Error Employee Documents")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_employee_certificates():
	try:
		data = json.loads(frappe.request.data)
		employee = data.get("employee")
		data = frappe.db.get_all("Employee Education", {
			"parent": employee,
		}, ["school_univ", "qualification", "year_of_passing", "custom_certificate"])
		if not data:
			return {"success": False, "error": "No Employee Certificates Found"}
		for row in data:
			file_url = row.get("custom_certificate")
			if not file_url:
				row["attachment"] = ""
				continue

			file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
			file_is_private = file_url.startswith("/private/files/")
			full_path = frappe.utils.get_files_path(file_name, is_private=file_is_private)
			
			file = open(full_path, 'rb')
			try:
				file_content = file.read()
			finally:
				file.close()

			row["attachment"] = base64.b64encode(file_content).decode('utf-8')
		
		return {
			"success": True,
			"data": data
		}
				
	except Exception as e:
		frappe.log_error(str(e), "Error Employee Documents")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_employee_family():
	try:
		data = json.loads(frappe.request.data)
		employee = data.get("employee")
		data = frappe.db.get_all("Employee Family", {
			"parent": employee,
		}, ["type", "name1 as name", "file", "remarks"])
		if not data:
			return {"success": False, "error": "No Employee Certificates Found"}
		for row in data:
			file_url = row.get("file")
			if not file_url:
				row["attachment"] = ""
				continue

			file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
			file_is_private = file_url.startswith("/private/files/")
			full_path = frappe.utils.get_files_path(file_name, is_private=file_is_private)
			
			file = open(full_path, 'rb')
			try:
				file_content = file.read()
			finally:
				file.close()

			row["attachment"] = base64.b64encode(file_content).decode('utf-8')
		
		return {
			"success": True,
			"data": data
		}
				
	except Exception as e:
		frappe.log_error(str(e), "Error Employee Documents")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_face_recognition():
	try:
		data = json.loads(frappe.request.data)
		employee = data.get("employee")
		current_image = data.get("image")
		file_url = frappe.db.get_value('Employee', employee, "image")
		if not file_url:
			return {"success": False, "error": "Employee image missing"}

		file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
		file_is_private = file_url.startswith("/private/files/")
		full_path = frappe.utils.get_files_path(file_name, is_private=file_is_private)
		current_path = save_base64_to_file(current_image, 'jpg')
		result = is_recognized(full_path, current_path)

		return { "is_recognized" : result }

	except Exception as e:
		frappe.log_error(str(e), "Error Get Employee Image")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_attendance_calendar_events():
	data = json.loads(frappe.request.data)
	employee = data.get("employee")
	from_date = data.get("from_date")
	to_date = data.get("to_date")
	holidays = get_holidays_for_calendar(employee, from_date, to_date)
	attendance = get_attendance_for_calendar(employee, from_date, to_date)
	events = {}

	date = getdate(from_date)
	while date_diff(to_date, date) >= 0:
		date_str = date.strftime("%Y-%m-%d")
		if date in holidays:
			events[date_str] = {"status": "Holiday"}
		if date in attendance:
			events[date_str] = attendance[date]
		date = add_days(date, 1)

	return events