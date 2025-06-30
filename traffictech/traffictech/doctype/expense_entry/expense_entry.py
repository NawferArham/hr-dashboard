# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

from openai import OpenAI

import base64
from io import BytesIO
from PIL import Image, ImageOps
import json
import os
import pypdfium2 as pdfium
import numpy as np
import re
import frappe
from frappe import _
from frappe.utils import flt, get_link_to_form
from frappe.model.document import Document
import pytesseract
from frappe.integrations.utils import get_json
from frappe.utils.password import get_decrypted_password

class ExpenseEntry(Document):
	def validate(self):
		self.calculate_total()
		self.check_category()
		self.calculate_conversion_total()
		self.get_user_employee()
		self.format_json_data()
		self.validate_supplier_invoice()
		# self.update_business_trip()
	
	def on_submit(self):
		self.validate_mandatory_fields()
		self.validate_conversion_rate()

	@frappe.whitelist()
	def check_category(self):
		if self.category:
			alert = frappe.db.get_value("Expense Category", self.category, "alert_category")
			if alert:
				frappe.msgprint(
                	_("This Expense Entry belongs to the '{0}' category. Please verify the document before submitting.").format(self.category)
            	)
				
	def get_user_employee(self):
		if not self.employee:
			employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
			if employee:
				self.employee = employee

		if not self.applying_for_another_employee:
			self.sub_employee = ""
			self.sub_employee_name = ""
	
	def validate_conversion_rate(self):
		company_currency = "QAR"
		if self.currency != company_currency:
			if not self.conversion_rate:
				frappe.throw(_("Please Set Currency Exchange Rate."))

		
	def validate_mandatory_fields(self):
		fields = ["employee", "supplier", "supplier_invoice_date", "currency", "supplier_invoice_no", "category"]
		for d in fields:
			if not self.get(d):
				field_label = self.meta.get_label(d)
				frappe.throw(_("{0} is mandatory.").format(field_label))	

		if not self.items:
			frappe.throw(_("Items Mandatory"))

	def validate_supplier_invoice(self):
		if self.supplier_invoice_no:

			ee = frappe.db.sql(
				"""select name from `tabExpense Entry`
				where
					supplier_invoice_no = %(supplier_invoice_no)s
					and supplier = %(supplier)s
					and name != %(name)s
					and docstatus < 2""",
				{
					"supplier_invoice_no": self.supplier_invoice_no,
					"supplier": self.supplier,
					"name": self.name,
				},
			)

			if ee:
				ee = ee[0][0]

				frappe.throw(
					_("Supplier Invoice No exists in Expense Entry {0}").format(
						get_link_to_form("Expense Entry", ee)
					)
				)


	def format_json_data(self):
		if self.json_data:
			data = json.loads(self.json_data)
			self.json_data = get_json(data)

	def calculate_total(self):
		for d in self.items:
			d.amount = flt(d.qty) * flt(d.rate)
		
		self.total_qty = sum(flt(d.qty) for d in self.items)
		self.total = sum(flt(d.amount) for d in self.items)

		self.net_total = flt(self.total) - flt(self.discount_amount)

		self.grand_total = flt(self.net_total) + flt(self.tax_and_charges)
	
	def calculate_conversion_total(self):
		if not self.conversion_rate:
			self.conversion_rate = 1
		for d in self.items:
			d.base_rate = flt(d.rate) * flt(self.conversion_rate, 9)
			d.base_amount = flt(d.qty) * flt(d.base_rate)
		
		self.base_total = sum(flt(d.base_amount) for d in self.items)

		self.base_discount_amount = flt(self.discount_amount) * flt(self.conversion_rate, 9)

		self.base_net_total = flt(self.base_total) - flt(self.base_discount_amount)

		self.base_tax_and_charges = flt(self.tax_and_charges) * flt(self.conversion_rate, 9)

		self.base_grand_total = flt(self.base_net_total) + flt(self.base_tax_and_charges)


	@frappe.whitelist()
	def ocr_document_file(self, file_url):
		file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
		file_is_private = file_url.startswith("/private/files/")
		FILE_PATH = frappe.utils.get_files_path(file_name, is_private=file_is_private)

		if not os.path.exists(FILE_PATH):
			frappe.throw("File does not exist")

		images = convert_to_image(FILE_PATH)

		image_preprocess = [
			pil_to_high_res,
			auto_crop_image,
			pil_to_grayscale,
			pil_to_invert,
			correct_image_orientation,
			convert_to_base64,
		]

		outputs = []
		for image in images:
			for pre_process in image_preprocess:
				try:
					image = pre_process(image)
				except Exception as e:
					frappe.log_error("Error OCR Single Page", str(e))
					continue

			try:
				output = AI_OCR(image)
				validate_output(output)
				outputs.append(output)
			except Exception as e:
				frappe.log_error("Error OCR Single Page", str(e))
				continue

		return output


	def update_business_trip(self):
		status = "Pending"
		if self.get("workflow_state") and "Rejected" in self.get("workflow_state"):
			status = "Rejected"
		if self.docstatus == 1:
			status = "Approved"
		
		frappe.db.set_value(
			"Business Employee Expense", 
			{"expense_entry": self.name}, 
			"status", 
			status
		)


@frappe.whitelist()
def create_multi_page_ocr(file_url):
	file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
	file_is_private = file_url.startswith("/private/files/")
	FILE_PATH = frappe.utils.get_files_path(file_name, is_private=file_is_private)

	if not os.path.exists(FILE_PATH):
		frappe.throw("File does not exist")

	images = convert_to_image(FILE_PATH)

	image_preprocess = [
		pil_to_high_res,
		auto_crop_image,
		pil_to_grayscale,
		pil_to_invert,
		correct_image_orientation,
		convert_to_base64,
	]

	for image in images:
		for pre_process in image_preprocess:
			try:
				image = pre_process(image)
			except Exception as e:
				frappe.log_error("Error OCR Multi Page", str(e))
				continue

		try:
			output = AI_OCR(image)
			validate_output(output)
			create_expense_entry(output)
		except Exception as e:
			frappe.log_error("Error OCR Multi Page", str(e))
			continue
	
	return True

def create_expense_entry(output):
	frappe.log_error("OCR Multi Page Data", str(output))
	output = frappe.parse_json(output)
	doc = frappe.new_doc("Expense Entry")
	doc.json_data = json.dumps(output)
	doc.supplier = output.supplier
	doc.supplier_invoice_date = output.date
	doc.supplier_invoice_no = output.supplier_invoice_no
	doc.currency = output.currency

	for row in output.get("items"):
		add_child = doc.append("items", {})
		add_child.description = row.get("description")
		add_child.qty = row.get("qty")
		add_child.rate = row.get("rate")

	doc.tax_and_charges = output.tax
	doc.discount_amount = output.discount
	doc.flags.ignore_validate = True
	doc.calculate_total()
	doc.format_json_data()
	doc.insert()
	return doc.name


def pil_to_high_res(image, scale_factor=2):
	# Calculate new dimensions
	new_width = int(image.width * scale_factor)
	new_height = int(image.height * scale_factor)

	# Resize the image using high-quality resampling
	high_res_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

	return high_res_image

def convert_to_image(file_path):
	extension = os.path.splitext(file_path)[1].lower()
	
	if extension in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
		image = Image.open(file_path)
		return [image]
	elif extension == ".pdf":
		pdf = pdfium.PdfDocument(file_path)
		imgs = []
		for p in pdf:
			imgs.append(p.render(scale=4).to_pil())
		return imgs
	else:
		raise ValueError("Unsupported file format. Only images and PDFs are supported.")

def auto_crop_image(pil_image, padding=10):
	# Convert the image to grayscale for simpler content detection
	gray = pil_image.convert("L")
	# Make a NumPy array
	arr = np.array(gray)
	
	# Create a mask of all pixels that are not "white"
	# i.e., anything less than 255 in grayscale is considered "content"
	mask = arr < 255
	
	# Find the row/column indices where mask is True
	coords = np.argwhere(mask)
	if coords.size == 0:
		# No content found
		return pil_image
	
	# coords is an N×2 array of (row, col) indices. 
	# Get the min/max row and min/max col to define the bounding box.
	rows, cols = coords[:,0], coords[:,1]
	top, left = rows.min(), cols.min()
	bottom, right = rows.max(), cols.max()
	
	# Apply padding (clamping to image boundaries)
	top = max(top - padding, 0)
	left = max(left - padding, 0)
	bottom = min(bottom + padding, arr.shape[0])
	right = min(right + padding, arr.shape[1])
	
	# Crop the original image. 
	# Remember PIL crop box is (left, upper, right, lower).
	cropped = pil_image.crop((left, top, right, bottom))
	return cropped

def pil_to_grayscale(image):
	return image.convert("L")

def pil_to_invert(image):
	return ImageOps.invert(image)

def correct_image_orientation(pillow_image):
	"""
	Combine both the contour-based deskew and Tesseract-based orientation
	into a single function.

	1) Deskew small angles using contours (deskew_by_contours).
	2) Correct 90/180/270-degree orientations using Tesseract OSD.

	Returns:
		PIL.Image.Image - final corrected image
	"""
	# Step 1: Deskew small angles
	deskewed_image = deskew_by_contours(pillow_image)

	# Step 2: Correct orientation with Tesseract
	final_corrected_image = correct_text_orientation_tesseract(deskewed_image)

	return final_corrected_image

def correct_text_orientation(pillow_image):
	"""
	Detect and correct the orientation of text in a Pillow Image using Tesseract OCR.

	Args:
		pillow_image (PIL.Image.Image): Input Pillow Image.

	Returns:
		PIL.Image.Image: Corrected Pillow Image with proper text orientation.
	"""
	try:
		# Use Tesseract to detect orientation
		ocr_data = pytesseract.image_to_osd(pillow_image)
		rotation_angle = int(ocr_data.split("Rotate: ")[1].split("\n")[0])

		# Rotate the image if the angle is not 0
		if rotation_angle != 0:
			corrected_image = pillow_image.rotate(-rotation_angle, expand=True)
			print(f"Image rotated by {-rotation_angle} degrees to correct text orientation.")
		else:
			corrected_image = pillow_image
			print("No rotation needed; text orientation is already correct.")

		return corrected_image

	except Exception as e:
		print(f"Error in text orientation correction: {e}")
		return pillow_image

def convert_to_base64(image):
	buffered = BytesIO()
	image.save(buffered, format="JPEG")
	base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
	return f"data:image/jpeg;base64,{base64_str}"

def AI_OCR(img_base64):
	base64_str = resize_image_base64(img_base64)

	categories_text = frappe.db.get_all("Expense Category", pluck="name")

	system_prompt = f"""
		You are an advanced OCR AI model designed to extract structured data from invoices. 
		Your task is to analyze the provided invoice image and generate a JSON object with the given structure:
		Rules:
		1. Extract all relevant details from the invoice, including supplier name, invoice date, and invoice number.
		2. Identify all line items (description, quantity, rate, and amount).
		3. Calculate subtotal, tax, and grand total if not explicitly provided.
		4. Ensure all fields are correctly formatted and complete.
		5. If a field is missing in the invoice, leave it empty or default to 0.
		6. If numbers are in arabic then understand it and accuratly convert it
		7. Understand the invoice list, text then do calculation
		8. Find the correct Document Type, like weather it is Quotation, Purchase Order, Invoice or any bill.
		9. Assign the correct **Expense Category** based on the available categories.
			**Expense Category Prediction Rules:**
			- ONLY use one of the following categories: {categories_text}
			- DO NOT generate new categories that are not listed.
			- If no relevant category is found, return "Other".           
        Follow these rules strictly and do NOT invent new Expense categories.

		Provide the output strictly in the above JSON structure without additional text or explanations.
	"""
	OPENAI_API_KEY = get_decrypted_password("OCR Settings", "OCR Settings", "api_key", raise_exception=False)
	client = OpenAI(api_key=OPENAI_API_KEY)

	response = client.chat.completions.create(
		model="gpt-4o",
		messages=[
			{
				"role": "user", 
				"content": [
					{ 
						"type": "text", 
						"text": system_prompt
					}, 
					{
						"type": "image_url", 
						"image_url": { "url": base64_str  , "detail": "high" }
					}, 
				]
			}
		],       
		temperature=0.3,
		max_completion_tokens=1024,
		response_format={
				"type": "json_schema",
				"json_schema": {
				"name": "invoice_schema",
				"schema": {
					"type": "object",
					"properties": {
					"category": {
						"type": "string",
						"description": "Predicted Expense Category from the provided list"
					},
					"document_type": {
						"type": "string",
						"description": "Document Type, like weather it is Quotation, Purchase Order, Invoice, Payment Receipt or any bill"
					},
					"supplier": {
						"type": "string",
						"description": "Supplier name"
					},
					"date": {
						"type": "string",
						"format": "date",
						"description": "Invoice date in YYYY-MM-DD format"
					},
					"supplier_invoice_no": {
						"type": "string",
						"description": "Invoice number"
					},
					"currency": {
						"type": "string",
						"description": "Currency code (e.g., QAR, USD)"
					},
					"items": {
						"type": "array",
						"description": "List of invoice items",
						"items": {
						"type": "object",
						"properties": {
							"description": {
							"type": "string",
							"description": "Item description"
							},
							"qty": {
							"type": "number",
							"description": "Quantity of the item"
							},
							"rate": {
							"type": "number",
							"description": "Rate per item"
							},
							"amount": {
							"type": "number",
							"description": "Total amount for this item"
							}
						},
						"required": ["description", "qty", "rate", "amount"],
						"additionalProperties": False
						}
					},
					"discount": {
						"type": "number",
						"description": "Total discount"
					},
					"subtotal": {
						"type": "number",
						"description": "Subtotal amount"
					},
					"tax": {
						"type": "number",
						"description": "Tax amount"
					},
					"grand_total": {
						"type": "number",
						"description": "Grand total amount"
					},
					"total_quantity": {
						"type": "number",
						"description": "Total quantity of all items"
					}
					},
					"required": [
						"supplier",
						"date",
						"supplier_invoice_no",
						"currency",
						"items",
						"discount",
						"subtotal",
						"tax",
						"grand_total",
						"total_quantity",
						"category",
						"document_type",
					],
					"additionalProperties": False
				}
			}
		},
		seed=456,
	)
	token = response.usage.total_tokens
	output =  json.loads(response.choices[0].message.content)

	return output

def resize_image_base64(base64_str, max_size=2000):
	"""
	Resizes an image (given in base64 format) to fit within max_size while maintaining the aspect ratio.

	:param base64_str: Base64 string of the image (with 'base64,' prefix expected)
	:param max_size: Maximum width or height of the resized image (default: 800px)
	:return: Resized image encoded as a base64 string
	"""
	# Ensure the base64 string has the 'base64,' prefix
	if "base64," in base64_str:
		start, image_data = base64_str.split("base64,")
		start = start + "base64,"
	else:
		raise ValueError("Invalid base64 string. Expected 'base64,' prefix.")

	# Decode the base64 string to an image
	image_data = base64.b64decode(image_data)
	image = Image.open(BytesIO(image_data))

	# Calculate the new size while maintaining aspect ratio
	aspect_ratio = image.width / image.height
	if image.width > image.height:
		new_width = min(max_size, image.width)
		new_height = int(new_width / aspect_ratio)
	else:
		new_height = min(max_size, image.height)
		new_width = int(new_height * aspect_ratio)

	# Resize the image using high-quality resampling
	resized_image = image.resize((new_width, new_height), Image.LANCZOS)

	# Save the resized image to a bytes buffer
	buffered = BytesIO()
	resized_image.save(buffered, format="PNG")

	# Encode the resized image back to base64
	resized_base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

	# Return the resized base64 string with the prefix
	return start + resized_base64_str



def validate_output(output):
	"""
	Validates the output JSON structure generated by the OCR process.

	:param output: The JSON object to validate
	:return: True if the output is valid, raises a ValueError otherwise
	"""
	required_fields = {
		"supplier": str,
		"date": str,
		"supplier_invoice_no": str,
		"currency": str,
		"items": list,
		"discount": (int, float),
		"subtotal": (int, float),
		"tax": (int, float),
		"grand_total": (int, float),
		"total_quantity": (int, float),
	}

	# Validate top-level fields
	for field, expected_type in required_fields.items():
		if field not in output:
			raise ValueError(f"Missing required field: '{field}'")
		if not isinstance(output[field], expected_type):
			raise ValueError(f"Field '{field}' must be of type {expected_type.__name__}, got {type(output[field]).__name__}")

	# Validate the items list
	for item in output["items"]:
		if not isinstance(item, dict):
			raise ValueError(f"Each item in 'items' must be a dictionary, got {type(item).__name__}")
		
		# Validate item fields
		required_item_fields = {
			"description": str,
			"qty": (int, float),
			"rate": (int, float),
			"amount": (int, float),
		}
		for field, expected_type in required_item_fields.items():
			if field not in item:
				raise ValueError(f"Missing required field in 'items': '{field}'")
			if not isinstance(item[field], expected_type):
				raise ValueError(f"Field '{field}' in 'items' must be of type {expected_type.__name__}, got {type(item[field]).__name__}")

	# Additional validation rules
	try:
		# Validate date format (YYYY-MM-DD)
		from datetime import datetime
		datetime.strptime(output["date"], "%Y-%m-%d")
	except ValueError:
		raise ValueError("Field 'date' must be in YYYY-MM-DD format")

	# Ensure numerical values are non-negative
	for field in ["discount", "subtotal", "tax", "grand_total", "total_quantity"]:
		if output[field] < 0:
			raise ValueError(f"Field '{field}' must be non-negative, got {output[field]}")

	# All checks passed
	return True