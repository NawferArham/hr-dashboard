# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

import frappe

def set_bootinfo(bootinfo):
	bootinfo["live_detection"] = frappe.db.get_value(
		"OCR Settings", 
		"OCR Settings", 
		"live_detection"
	)

	# for temporary toggle for fsm final report
	bootinfo["enable_pdf_download"] = frappe.db.get_value(
		"OCR Settings", 
		"OCR Settings", 
		"enable_pdf_download"
	)