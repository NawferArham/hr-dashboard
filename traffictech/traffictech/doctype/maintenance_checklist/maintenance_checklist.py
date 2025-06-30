# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaintenanceChecklist(Document):
	@frappe.whitelist()
	def fetch_template(self, templates):
		self.set("main_activities", [])
		self.set("sub_activities", [])
		for template in templates:
			if not template:
				continue

			activities = frappe.db.get_all(
				"Maintenance Checklist Template Activity",
				{"parent": template},
				pluck="activity",
				order_by="idx"
			)

			self.append("main_activities", {
				"activity": template,
				"divider": 1                  # to highlight
			})

			for act in activities:
				self.append("main_activities", {
					"activity": act,
					"template": template,
				})

				sub_activities = frappe.db.get_all(
					"Maintenance Checklist Template Sub Activity",
					{"parent": act, "parenttype": "Maintenance Checklist Activity"},
					["activity", "check", "comments"],
					order_by="idx",
				)

				for sub_act in sub_activities:
					self.append("sub_activities", {
						"activity": sub_act.activity,
						"parent_activity": act,
						"check": sub_act.check,
						"comments": sub_act.comments,
					})