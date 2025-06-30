# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

import json
import frappe
from openai import OpenAI
from frappe.utils.password import get_decrypted_password



def set_email_category(doc, method=None):
	# if doc.sent_or_received == "Received":
	category = classify_email_content(doc.subject, doc.content)
	if category:
		doc.db_set("custom_category", category)


def classify_email_content(email_subject, email_body):
	"""Classifies email content into predefined categories using OpenAI."""

	email_categories = frappe.db.get_all("Email Category", ["name", "description"])
	categories_text = "\n".join([f"- {cat['name']}: {cat['description']}" for cat in email_categories])

	
	system_prompt = f"""
	Classify the following email into categories such as: {categories_text}.
	Email Subject: {email_subject}
	Email Body: {email_body}
	**Email Category Prediction Rules:**
	- DO NOT generate new categories that are not listed.
		- If no relevant category is found, return "Other".

	Provide the output strictly in the above JSON structure without additional text or explanations.
	"""

	OPENAI_API_KEY = get_decrypted_password("OCR Settings", "OCR Settings", "api_key", raise_exception=False)
	client = OpenAI(api_key=OPENAI_API_KEY)
	
	try:
		response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
				{
					"role": "user", 
					"content": [
						{ 
							"type": "text", 
							"text": system_prompt
						} 
					]
				}
			],
            max_tokens=50,
            temperature=0.7,
			response_format={
                "type": "json_schema",
				"json_schema": {
					"name": "category_schema",
					"schema": {
						"type": "object",
						"properties": {
							"category": {
								"type": "string",
								"description": "Predicted Email Category from the provided list"
							}
						},
						"required": ["category"],  
						"additionalProperties": False
					}
				}
            }
        )
		output =  json.loads(response.choices[0].message.content)
		return output.get("category","")
	except Exception as e:
		frappe.log_error("Error classifying email", str(e))


def make_file_private(doc, method=None):
	if doc.is_private:
		return

	if doc.attached_to_doctype == "Petty Cash Entry" and not doc.is_private:
		doc.is_private = 1
		doc.save()


def calculate_ssa_total(doc, method=None):
	total = 0.0
	total += doc.base

	if doc.meta.has_field("custom_housing_allowance"):
		total += doc.custom_housing_allowance
	if doc.meta.has_field("custom_food_allowance"):
		total += doc.custom_food_allowance
	
	if doc.meta.has_field("custom_transportation_allowance"):
		total += doc.custom_transportation_allowance
	
	if doc.meta.has_field("custom_mobile_allowance"):
		total += doc.custom_mobile_allowance

	if doc.meta.has_field("custom_driving_allowance"):
		total += doc.custom_driving_allowance

	if doc.meta.has_field("custom_education_allowance"):
		total += doc.custom_education_allowance

	if doc.meta.has_field("custom_other_allowance"):
		total += doc.custom_other_allowance
	
	if doc.meta.has_field("custom_overtime_allowance"):
		total += doc.custom_overtime_allowance

	doc.custom_total = total


def get_ctc_from_ssa(doc, method=None):
	ctc = frappe.db.get_value("Salary Structure Assignment", {
		"employee": doc.name,
		"docstatus": 1
	}, "custom_total", order_by="from_date desc") or 0
	doc.ctc =  ctc


def set_ctc_in_emp(doc, method=None):
	ctc = frappe.db.get_value("Salary Structure Assignment", {
		"employee": doc.employee,
		"docstatus": 1
	}, "custom_total", order_by="from_date desc") or 0
	frappe.db.set_value("Employee", doc.employee, "ctc", ctc)