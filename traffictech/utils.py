"""
{
	"supplier": "Lulu",
	"date": "2025-01-25",
	"supplier_invoice_no": "ACC-PI-0001",
	"currency": "QAR",
	"items": [
		"description": "Air Ticket",
		"qty": 1,
		"rate": 200,
		"amount": 200
	]
}
"""


# -*- coding: utf-8 -*-
"""sample_code_ocr_extraction.ipynb

Automatically generated by Colab.

Original file is located at
	https://colab.research.google.com/drive/1iitIxkD2vMuoWAGJmcRJC9fygRcuRpRh
"""

import cv2
import pytesseract
from PIL import Image
import numpy as np
import re
import frappe
from frappe.utils import flt
from frappe import _
from frappe.www.login import _generate_temporary_login_link


def get_image_data(image):

	image = Image.open('')

	custom_config = r'--oem 1 --psm 6'
	text = pytesseract.image_to_string(image, config=custom_config, lang='eng+ara')  # Specify both languages

	print("Extracted Text:\n", text)

	invoice_data = extract_invoice_data(text)
	print(invoice_data)




def extract_invoice_data(text):

	invoice_data = {}

	# Extract Supplier Name (First prominent line with capitalized words)
	supplier_match = re.match(r"([A-Za-z0-9\s&.-]+())", text)
	if supplier_match:
		invoice_data['supplier'] = supplier_match.group(0).strip()

	# Extract Date (dd/mm/yyyy, dd.mm.yyyy, or ddth Month yyyy)
	date_match = re.search(
		r"\b(?:\d{1,2}[/.]\d{1,2}[/.]\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})\b", text
	)
	if date_match:
		invoice_data['date'] = date_match.group(0).strip()

	# Extract Item Description (Lines containing alphanumeric text followed by a price)
	item_description_match = re.search(r"([A-Za-z0-9\s])", text)
	if item_description_match:
		invoice_data['item description'] = item_description_match.group(0).strip()

	# Extract Total Amount (Supports formats like "QAR 3699.00" or "3699.00 QAR")
	total_amount_match = re.search(
		r"(?:(?:[A-Z]{2,3}\s*)?[\d,]+\.\d{2}\s*(?:[A-Z]{2,3})?)", text
	)
	if total_amount_match:
		invoice_data['total amount'] = total_amount_match.group(0).strip()

	return invoice_data


@frappe.whitelist()
def download_pm_final_report(doctype, docname):
	doc = frappe.get_doc(doctype, docname)
	asset_unit = frappe.db.get_value(
		"Asset Unit", 
		doc.asset_unit, 
		["asset_id", "asset_name", "junction_no"], 
		as_dict=1
	)
	pdf_file = frappe.get_print(
		doctype,
		doc.name,
		doc=doc,
		as_pdf=True,
	)

	name = f"{asset_unit.asset_name}-{asset_unit.junction_no}.pdf"
	if asset_unit.asset_id:
		name = f"{asset_unit.asset_id}-{asset_unit.asset_name}-{asset_unit.junction_no}.pdf"

	frappe.local.response.filename = name
	frappe.local.response.filecontent = pdf_file
	frappe.local.response.type = "pdf"


@frappe.whitelist()
def get_opporunity_stages(doctype, txt, searchfield, start, page_len, filters):
	stages = frappe.db.get_all(
		"Pipeline Opportunity Stage", 
		{"parent": filters.get("pipeline")},
		["stage"],
		order_by="idx",
		as_list=1
	)

	return stages


@frappe.whitelist()
def get_probability(pipeline, stage):
	stages = frappe.db.get_all(
		"Pipeline Opportunity Stage", 
		{"parent": pipeline},
		["stage", "probability"],
		order_by="idx",
	)

	probability = 0
	for row in stages:
		probability += flt(row.probability)

		if row.stage == stage:
			break

	return probability


@frappe.whitelist()
def get_ssa_of_emp(employee):
	ssa = frappe.db.get_value("Salary Structure Assignment", {
		"employee": employee,
		"docstatus": 1
	}, "name", order_by="from_date desc") or 0
	return ssa


def set_home_page(login_manager):
	roles = frappe.get_roles()
	if "System Manager" in roles:
		return

	if "HR Manager" in roles:
		frappe.local.response["home_page"] = "/app/hr-manager-dashboard"
	
	if "Employee" in roles and "HR Manager" not in roles:
		frappe.local.response["home_page"] = "/app/employee-dashboard"


@frappe.whitelist()
def generate_impersonation_url(user):
	frappe.only_for("System Manager")

	if user == "Administrator":
		frappe.throw(_("You cannot impersonate Administrator"))

	return _generate_temporary_login_link(user, 1)