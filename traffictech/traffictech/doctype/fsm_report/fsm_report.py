# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path
import base64



class FSMReport(Document):
	@frappe.whitelist()
	def replace_existing_file(self, file_url, filedata_base64):
		"""Replace an existing file's content with new base64 file"""
		# Find the File doc
		file_doc = frappe.db.get_value("File", {"file_url": file_url}, "file_url")
		if not file_doc:
			frappe.throw(f"File not found: {file_url}")

		# Decode base64
		file_path = get_file_path(file_url)
		file_content = base64.b64decode(filedata_base64)

		# Overwrite the file
		with open(file_path, 'wb') as f:
			f.write(file_content)

		return {"file_url": file_doc}
