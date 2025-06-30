# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add
from frappe.utils import format_date
from frappe import _


class CorrectiveMaintenanceRequest(Document):
	def validate(self):
		# to avoid the naming issue if data imported
		if "00:00:00" in self.name and self.is_new():
			name = self.name.replace(" 00:00:00", "")
			self.name = name

		self.validate_schedule()

	def on_submit(self):
		self.create_tasks()

	def on_cancel(self):
		self.update_ref_doc_status()
	
	def update_ref_doc_status(self):
		frappe.db.set_value(
			"Task", 
			{"cm_request": self.name}, 
			"status", 
			"Rejected"
		)
		frappe.db.set_value(
			"Corrective Maintenance", 
			{"cm_request": self.name}, 
			"status", 
			"Cancelled"
		)

	def validate_schedule(self):
		if not self.units:
			return

		units = []
		for unit in self.units:
			units.append(unit.asset_unit)

		cmr = frappe.qb.DocType("Corrective Maintenance Request")
		un = frappe.qb.DocType("Schedule Cabinet Item")
		exists = (
			frappe.qb.from_(cmr)
			.inner_join(un).on((cmr.name == un.parent) & (un.parenttype == "Corrective Maintenance Request"))
			.select(
				cmr.name,
				cmr.posting_date,
				un.asset_unit,
			)
			.where(
				(un.asset_unit.isin(units)) &
				(cmr.team == self.team) &
				(cmr.posting_date == self.posting_date) &
				(cmr.docstatus < 2) &
				(cmr.name != self.name)
			)
			.run(as_list=1)
		)
		if exists and not self.get("from_bulk"):
			frappe.throw(
				_(
					"Asset Unit {0} is already Requested by this Team on {1} <br> Reference: {2}"
					.format(
						frappe.bold(exists[0][2]),
						format_date(exists[0][1]),
						frappe.bold(frappe.get_desk_link("Corrective Maintenance Request", exists[0][0]))
					)
				)
			)
	
	def create_tasks(self):
		team_members = []
		for row in self.team_members:
			team_members.append(row.user_id)
		
		for row in self.units:
			task = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": "CM-" + row.asset_name + " : " + self.team,
					"project": row.project,
					"description": row.asset_name,
					"cm_request": self.name,
					"asset_unit": row.asset_unit,
					"team": self.team,
					"type": "CM",
					"incident_type": self.incident_type,
					"incident_category": self.incident_category,
				}
			)
			task.db_set("project", row.project)
			task.insert(ignore_permissions=True)

			self.assign_task_to_users(task, team_members)

		if not self.units:
			task = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": "CM-" + self.incident_category + " : " + self.team,
					"description": self.incident_category,
					"cm_request": self.name,
					"team": self.team,
					"type": "CM",
					"incident_type": self.incident_type,
					"incident_category": self.incident_category,
				}
			)
			task.insert(ignore_permissions=True)

			self.assign_task_to_users(task, team_members)
		
	def assign_task_to_users(self, task, users):
		args = {
			"assign_to": users,
			"doctype": task.doctype,
			"name": task.name,
			"description": task.description or task.subject,
		}
		add(args)

	@frappe.whitelist()
	def add_team_members(self):
		if not self.team:
			return
		
		team_members = frappe.db.get_all(
			"Team Member", 
			{"parent": self.team}, 
			["member", "user_id", "engineer_in_charge"]
		)

		exis_members = []
		for row in self.team_members:
			exis_members.append(row.member)

		for member in team_members:
			if member not in exis_members:
				self.append("team_members", {
					"member": member.member,
					"user_id": member.user_id,
					"engineer_in_charge": member.engineer_in_charge
				})

	@frappe.whitelist()
	def change_team(self, team, bulk=False):
		"""
		This function used to change the assigned team of a schedule
		"""

		if self.team == team and not bulk:
			frappe.throw("Cannot select same Team!")

		tasks = frappe.db.get_all(
			'Task', 
			{"cm_request": self.name}, 
			["status", "name", "description", "subject", "asset_name"]
		)

		# Get new team members
		members = frappe.db.get_all(
			"Team Member",
			{"parenttype": "Team", "parent": team},
			["member", "member_name", "user_id", "engineer_in_charge"]
		)
		users = []

		self.db_set("team", team)
		self.team_members = []
		for member in members:
			self.append("team_members", {
				"member": member.member,
				"user_id": member.user_id,
				"engineer_in_charge": member.engineer_in_charge
			})
			users.append(member.user_id)

		self.flags.ignore_validate = True
		self.flags.ignore_validate_update_after_submit = True
		self.flags.ignore_on_update = True
		self.save(ignore_permissions=True)

		for task in tasks:
			if task.status == "Completed":
				continue

			frappe.db.delete("ToDo", {"reference_type": "Task", "reference_name": task.name})
			frappe.db.set_value("Task", task.name, { "team":team, "subject": "CM-" + task.asset_name + " : " + team })

			# Assign new users to the Task
			args = {
				"assign_to": users,
				"doctype": "Task",
				"name": task.name,
				"description": task.description or task.subject,
			}
			add(args)
