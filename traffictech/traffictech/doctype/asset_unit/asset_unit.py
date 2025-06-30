# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from pyproj import Transformer
import frappe


class AssetUnit(Document):
	def validate(self):
		self.convert_coordinates()

	@frappe.whitelist()
	def convert_coordinates(self):
		if self.x_coordinate and self.y_coordinate:
			# Define the transformation from EPSG:2932 (Qatar National Grid) to EPSG:4326 (WGS 84)
			transformer = Transformer.from_crs("EPSG:2932", "EPSG:4326", always_xy=True)
			
			# Convert coordinates
			longitude, latitude = transformer.transform(float(self.x_coordinate), float(self.y_coordinate))
			
			self.longitude = longitude
			self.latitude = latitude

	@frappe.whitelist()
	def create_inspection_request(self):
		new_insp = frappe.new_doc("Inspection Improvement Request")
		new_insp.append("units", {
			"asset_unit": self.name,
			"asset_name": self.asset_name,
			"asset_id": self.asset_id,
			"asset_id": self.asset_id,
			"project": self.project,
		})
		return new_insp.as_dict()

	@frappe.whitelist()
	def sync_tasks(self):
		tasks = frappe.db.get_all("Task", 
			{"asset_unit": self.name, "status": ["!=", "Completed"]}, 
			pluck="name"
		)
		for task in tasks:
			task_doc = frappe.get_doc("Task", task)
			task_doc.save()

		return True

@frappe.whitelist()
def bulk_schedule_asset_unit(asset_units, team, schedule_date, schedule_month, fiscal_year):
	asset_units = frappe.parse_json(asset_units)
	sc = frappe.get_doc(
		{
			"doctype": "Schedule Cabinet",
			"date": schedule_date,
			"team": team,
			"month": schedule_month,
			"fiscal_year": fiscal_year,
		}
	)
	for unit in asset_units:
		sc.append("asset_units",
			{
				"asset_unit": unit
			}
		)

	team_members = frappe.db.get_all(
		"Team Member", 
		{"parent": team}, 
		["member", "user_id", "engineer_in_charge"]
	)
	for member in team_members:
		sc.append("team_members", {
			"member": member.member,
			"user_id": member.user_id,
			"engineer_in_charge": member.engineer_in_charge
		})

	sc.insert(ignore_permissions=True)
	sc.submit()