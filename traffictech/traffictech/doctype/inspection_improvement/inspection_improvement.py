# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, get_datetime, flt
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe import _
import base64
from frappe.utils.file_manager import get_file_path


class InspectionImprovement(Document):
	def autoname(self):
		if self.replacement:
			self.name = make_autoname(f"REPL-{self.project}-RFI-.####")
		else:
			self.name = make_autoname(f"{self.project}-RFI-.####")

	def validate(self):
		self.vaidate_attachments()
		self.calculate_boq_totals()

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

	@frappe.whitelist()
	def create_checklist(self):
		asset_details = frappe.db.get_value(
			"Asset Unit", 
			self.asset_unit, 
			["asset_name", "main_checklist", "device_checklist"],
			as_dict=1
		)
		new_checklist = frappe.new_doc("Maintenance Checklist")
		new_checklist.inspection_improvement = self.name
		new_checklist.team = self.team
		new_checklist.project = self.project

		templates = frappe.db.get_all(
			"Asset Unit Checklist Template", 
			{"parent": self.asset_unit}, 
			pluck="template", 
			order_by="idx"
		)
		new_checklist.fetch_template(templates)

		return new_checklist.as_dict()

	def calculate_boq_totals(self):
		self.total_amount = self.total_qty = 0
		for row in self.boq_items:
			row.amount = flt(row.qty) * flt(row.rate)
			self.total_amount += row.amount
			self.total_qty += row.qty

	@frappe.whitelist()
	def add_reference_documents(self):
		if not self.document_template:
			return
		
		documents = frappe.db.get_all("Inspection Improvement Documents", 
			{
				"parenttype": "Inspection Improvement Document Template", 
				"parent": self.document_template
			},
			["document", "comment"]
		)

		self.documents = []
		for row in documents:
			self.append("documents", row)

def update_inspection_improvement(task, status):
	existing_ins = frappe.db.get_value(
		"Inspection Improvement", 
		{
			"ins_imp_request": task.ins_imp_request, 
			"asset_unit": task.asset_unit, 
			"replacement": 1 if task.supervisor else 0,
			"docstatus": ["<", 2],
			# "date": task.posting_date,
		},
		["name", "docstatus", "team"],
		as_dict=1
	)
	
	if existing_ins and existing_ins.docstatus == 1:
		tasks = frappe.db.get_all(
			"Task", 
			{"ins_imp_request": task.ins_imp_request, "asset_unit": task.asset_unit, "team": task.team}, 
			["name", "total_time_taken"]
		)
		total_time = 0
		for task_ in tasks:
			total_time += flt(task_.total_time_taken)

		frappe.db.set_value("Inspection Improvement", existing_ins.name, {
				"total_time_taken": total_time,
				"status": status,
				"completed_date": task.completed_on,
			}
		)

		return

	if existing_ins:
		ins = frappe.get_doc("Inspection Improvement", existing_ins.name)
		ins.status = status

		# add team members
		if ins.team != task.team:
			ins.team = task.team
			ins.team_members = []
			team_members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": task.team},
				["member", "engineer_in_charge"]
			)
			for mem in team_members:
				ins.append("team_members", {
					"member": mem.member,
					"engineer_in_charge": mem.engineer_in_charge,
				})

		# add tasks
		ins.tasks = []
		tasks = frappe.db.get_all(
			"Task", 
			{"ins_imp_request": task.ins_imp_request, "asset_unit": task.asset_unit, "team": ins.team}, 
			["name", "total_time_taken"]
		)

		total_time = 0
		for task_ in tasks:
			ins.append("tasks", {
				"task": task_.name
			})
			total_time += flt(task_.total_time_taken)

		ins.total_time_taken = total_time

		if task.completed_on:
			ins.completed_date = task.completed_on

		ins.save()
	else:
		type_of_work = frappe.db.get_value(
			"Inspection Request Asset Unit", 
			{
				"parenttype": "Inspection Improvement Request",
				"parent": task.ins_imp_request,
				"asset_unit": task.asset_unit,
			},
			"type_of_work"
		)
		ins = frappe.get_doc({
			"doctype": "Inspection Improvement",
			"date": today(),
			"ins_imp_request": task.ins_imp_request,
			"asset_unit": task.asset_unit,
			"start_time": get_datetime(),
			"type_of_work": type_of_work,
			"end_time": "",
			"total_time_taken": "",
			"status": status,
			"replacement": 1 if task.supervisor else 0,
			"team": task.team,
		})

		team_members = frappe.db.get_all(
			"Team Member", 
			{"parent": task.ins_imp_request, "parenttype": "Inspection Improvement Request"}, 
			["member", "engineer_in_charge"]
		)

		if ins.replacement:
			team_members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": task.team},
				["member", "engineer_in_charge"]
			)

		for mem in team_members:
			ins.append("team_members", {
				"member": mem.member,
				"engineer_in_charge": mem.engineer_in_charge,
			})

		tasks = frappe.db.get_all(
			"Task", 
			{"ins_imp_request": task.ins_imp_request, "asset_unit": task.asset_unit}, 
			pluck="name"
		)
		for task in tasks:
			ins.append("tasks", {
				"task": task
			})

		ins.insert(ignore_permissions=True)
		ins.save()
