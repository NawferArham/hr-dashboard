# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaintenanceChecklistTemplate(Document):
	"""
		Currently all the template activities are adding to a single table, so it will be confusing which template activity is updating.
		So creating a new activity with same name of template and highlight in the table for better understanding.
		when updating the Checklist
	"""
	def after_insert(self):
		new_activity = frappe.new_doc("Maintenance Checklist Activity")
		new_activity.activity_name = self.name
		new_activity.insert(ignore_permissions=True)
