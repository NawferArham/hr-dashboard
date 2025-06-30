# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add
from frappe.utils import format_date
from frappe import _


class ScheduleCabinet(Document):
	def after_insert(self):
		"""
			When data importing this file, the child table not getting updated even after inserted.
			I think there is a bug in data import in insert record function: data_import/importer.py line 271
			there is only doc.insert() added not doc.save(), so when saving the tables are getting updated.
		"""
		self.save()

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
			{"schedule_cabinet": self.name}, 
			"status", 
			"Rejected"
		)
		frappe.db.set_value(
			"Preventive Maintenance", 
			{"schedule_cabinet": self.name}, 
			"status", 
			"Cancelled"
		)

	def validate_schedule(self):
		units = []
		for unit in self.asset_units:
			units.append(unit.asset_unit)

		sc = frappe.qb.DocType("Schedule Cabinet")
		un = frappe.qb.DocType("Schedule Cabinet Item")
		exists = (
			frappe.qb.from_(sc)
			.inner_join(un).on(sc.name == un.parent)
			.select(
				sc.name,
				sc.date,
				un.asset_unit,
			)
			.where(
				(un.asset_unit.isin(units)) &
				(sc.team == self.team) &
				(sc.date == self.date) &
				(sc.docstatus < 2) &
				(sc.name != self.name)
			)
			.run(as_list=1)
		)
		if exists and not self.get("from_bulk"):
			frappe.throw(
				_(
					"Asset Unit {0} is already Scheduled for this Team on {1} <br> Reference: {2}"
					.format(
						frappe.bold(exists[0][2]),
						format_date(exists[0][1]),
						frappe.bold(frappe.get_desk_link("Schedule Cabinet", exists[0][0]))
					)
				)
			)
	
	def create_tasks(self):
		team_members = []
		for row in self.team_members:
			team_members.append(row.user_id)
		
		for row in self.asset_units:
			task = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": "PM-" + row.asset_name + " : " + self.team,
					"project": row.project,
					"description": row.asset_name,
					"schedule_cabinet": self.name,
					"asset_unit": row.asset_unit,
					"team": self.team,
					"type": "PM",
				}
			)
			task.db_set("project", row.project)
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
			{"schedule_cabinet": self.name}, 
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
			frappe.db.set_value("Task", task.name, { "team":team, "subject": "PM-" + task.asset_name + " : " + team })

			# Assign new users to the Task
			args = {
				"assign_to": users,
				"doctype": "Task",
				"name": task.name,
				"description": task.description or task.subject,
			}
			add(args)


@frappe.whitelist()
def change_team_bulkly(schedules, team, from_task=False, type_="PM"):
	schedules = frappe.parse_json(schedules)
	from_task = frappe.parse_json(from_task)
	frappe.enqueue("traffictech.traffictech.doctype.schedule_cabinet.schedule_cabinet.change_team_assignment",
		schedules=schedules,
		team=team,
		from_task=from_task,
		type_=type_,
		queue='default'
	)

def change_team_assignment(schedules, team, from_task, type_):
	doctype_dict = {
		"PM": ["Schedule Cabinet", "schedule_cabinet"],
		"INS": ["Inspection Improvement Request", "ins_imp_request"],
		"CM": ["Corrective Maintenance Request", "cm_request"],
	}

	doc_type = doctype_dict.get(type_)
	for schedule in schedules:
		if from_task:
			task_type = frappe.db.get_value("Task", schedule, "type")
			doc_type = doctype_dict.get(task_type)

			schedule = frappe.db.get_value("Task", schedule, doc_type[1])

		doc = frappe.get_doc(doc_type[0], schedule)
		doc.from_bulk = True
		if doc.docstatus == 2:
			continue

		if not doc.docstatus and doc.team != team:
			doc.team = team

			# Get new team members
			members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": team},
				["member", "member_name", "user_id", "engineer_in_charge"]
			)

			for member in members:
				doc.append("team_members", {
					"member": member.member,
					"user_id": member.user_id,
					"engineer_in_charge": member.engineer_in_charge
				})

			doc.save()
		
		if doc.docstatus == 1:
			doc.change_team(team, bulk=True)