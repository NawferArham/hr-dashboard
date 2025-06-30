# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Team(Document):
	def validate(self):
		assinged_engineer = 0
		for row in self.team_member:
			if row.engineer_in_charge:
				assinged_engineer += 1

		if assinged_engineer > 1:
			frappe.throw("Cannot Assign more than one Engineer")

		if not assinged_engineer:
			frappe.throw("Assign one Engineer who is in Charge")