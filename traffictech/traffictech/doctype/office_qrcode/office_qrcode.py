# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
import uuid
from frappe.model.document import Document
from frappe.utils import get_datetime  


class OfficeQRCode(Document):
	# Generate a new QR code
	@frappe.whitelist()
	def generate_qr_code(self):
		# Fetch the validity duration from the Doctype
		validity_duration = self.interval
		last_modified_time = get_datetime(self.modified)

		current_time = get_datetime()

		time_difference_seconds = (current_time - last_modified_time).total_seconds()

		if time_difference_seconds > validity_duration:
			qr_value = str(uuid.uuid4())
			self.qrcode_data = qr_value
			self.save(ignore_permissions=True)
			return {"qr_code": qr_value, "validity": validity_duration}

		return {"qr_code": self.qrcode_data, "validity": validity_duration}