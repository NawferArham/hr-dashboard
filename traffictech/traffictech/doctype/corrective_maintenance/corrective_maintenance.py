# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, get_datetime, flt
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe import _
from frappe.utils.file_manager import get_file_path
import base64


class CorrectiveMaintenance(Document):
	def after_insert(self):
		"""
			When data importing this file, the child table not getting updated even after inserted.
			I think there is a bug in data import in insert record function: data_import/importer.py line 271
			there is only doc.insert() added not doc.save(), so when saving the tables are getting updated.
		"""
		self.save()

	def autoname(self):
		if self.replacement:
			self.name = make_autoname(f"REPL-CM-{self.cm_request}-.####")
		else:
			self.name = make_autoname(f"CM-{self.cm_request}-.####")

	def validate(self):
		self.vaidate_attachments()
		self.calculate_boq_totals()
		self.update_asset_units_to_tasks()

	def vaidate_attachments(self):
		if len(self.before) > 4 or len(self.during) > 4 or len(self.after) > 4:
			frappe.throw("Cannot Attach more than 4 Images, remove the last added row!")

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

	def calculate_boq_totals(self):
		self.total_amount = self.total_qty = 0
		for row in self.items:
			row.amount = flt(row.qty) * flt(row.rate)
			self.total_amount += row.amount
			self.total_qty += row.qty

	def update_asset_units_to_tasks(self):
		if not self.asset_unit:
			return

		tasks = frappe.db.get_all(
			"Task", 
			{
				"cm_request": self.cm_request, 
				"team": self.team,
				"incident_type": self.incident_type,
				"incident_category": self.incident_category,
				"asset_unit": ["=", ""],
			},
			pluck="name"
		)

		if not tasks:
			return
		
		asset_details = frappe.db.get_value(
			"Asset Unit", 
			self.asset_unit,
			["junction_no", "project", "longitude", "latitude"],
			as_dict=1
		)

		frappe.db.set_value("Task", 
			{"name": ["in", tasks]}, 
			{
				"asset_unit": self.asset_unit,
				"junction_no": asset_details.get("junction_no"),
				"project": asset_details.get("project"),
				"longitude": asset_details.get("longitude"),
				"latitude": asset_details.get("latitude"),
			}
		)


def update_corrective_maintenance(task, status):
	existing_cm = frappe.db.get_value(
		"Corrective Maintenance", 
		{
			"cm_request": task.cm_request, 
			"asset_unit": task.asset_unit if task.asset_unit else "",
			"replacement": 1 if task.supervisor else 0,
			"docstatus": ["<", 2],
			"incident_type": task.incident_type,
			"incident_category": task.incident_category,
		},
		["name", "docstatus", "team"],
		as_dict=1
	)
		
	if existing_cm and existing_cm.docstatus == 1:
		tasks = frappe.db.get_all(
			"Task", 
			{
				"cm_request": task.cm_request, 
				"asset_unit": task.asset_unit if task.asset_unit else "", 
				"team": task.team,
				"incident_type": task.incident_type,
				"incident_category": task.incident_category,
			},
			["name", "total_time_taken"]
		)
		total_time = 0
		for task_ in tasks:
			total_time += flt(task_.total_time_taken)

		frappe.db.set_value("Corrective Maintenance", existing_cm.name, {
				"total_time_taken": total_time,
				"status": status,
				"completed_date": task.completed_on,
			}
		)

		return

	if existing_cm:
		cm = frappe.get_doc("Corrective Maintenance", existing_cm.name)
		cm.status = status

		# add team members
		if cm.team != task.team:
			cm.team = task.team
			cm.team_members = []
			team_members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": task.team},
				["member", "engineer_in_charge"]
			)
			for mem in team_members:
				cm.append("team_members", {
					"member": mem.member,
					"engineer_in_charge": mem.engineer_in_charge,
				})

		# add tasks
		cm.tasks = []
		tasks = frappe.db.get_all(
			"Task", 
			{
				"cm_request": task.cm_request, 
				"asset_unit": task.asset_unit if task.asset_unit else "", 
				"team": cm.team,
				"incident_type": task.incident_type,
				"incident_category": task.incident_category,
			}, 
			["name", "total_time_taken"]
		)
		total_time = 0
		for task_ in tasks:
			cm.append("tasks", {
				"task": task_.name
			})
			total_time += flt(task_.total_time_taken)

		cm.total_time_taken = total_time

		if task.completed_on:
			cm.completed_date = task.completed_on

		cm.save()
	else:
		cm = frappe.get_doc({
			"doctype": "Corrective Maintenance",
			"date": today(),
			"cm_request": task.cm_request,
			"asset_unit": task.asset_unit,
			"start_time": get_datetime(),
			"end_time": "",
			"total_time_taken": "",
			"status": status,
			"replacement": 1 if task.supervisor else 0,
			"team": task.team,
			"incident_type": task.incident_type,
			"incident_category": task.incident_category,
		})

		team_members = frappe.db.get_all(
			"Team Member", 
			{"parent": task.cm_request, "parenttype": "Corrective Maintenance Request"}, 
			["member", "engineer_in_charge"]
		)

		if cm.replacement:
			team_members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": task.team},
				["member", "engineer_in_charge"]
			)

		for mem in team_members:
			cm.append("team_members", {
				"member": mem.member,
				"engineer_in_charge": mem.engineer_in_charge,
			})

		tasks = frappe.db.get_all(
			"Task", 
			{
				"cm_request": task.cm_request, 
				"asset_unit": task.asset_unit if task.asset_unit else "",
				"incident_type": task.incident_type,
				"incident_category": task.incident_category,
			}, 
			pluck="name"
		)
		for task in tasks:
			cm.append("tasks", {
				"task": task
			})

		cm.insert(ignore_permissions=True)
		cm.save()
