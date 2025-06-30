# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

import frappe
from traffictech.traffictech.doctype.preventive_maintenance.preventive_maintenance import (
	update_preventive_maintenance as update_pm
)
from traffictech.traffictech.doctype.inspection_improvement.inspection_improvement import (
	update_inspection_improvement as update_ins
)
from traffictech.traffictech.doctype.corrective_maintenance.corrective_maintenance import (
	update_corrective_maintenance as update_cm
)
from frappe.utils import time_diff_in_seconds, get_datetime, nowdate, today
from frappe.desk.form.assign_to import add
from frappe.utils import get_link_to_form

def update_ins_pm(doc, status):
	"""
	Common function to update Preventive Maintenance, Inpsection Improvemen and Corrective Maintenance
	"""
	if doc.schedule_cabinet:
		update_pm(doc, status=status)

	if doc.ins_imp_request:
		update_ins(doc, status=status)
	
	if doc.cm_request:
		update_cm(doc, status=status)
	

@frappe.whitelist()
def start_task(task_name):
	task = frappe.get_doc("Task", task_name)
	task.status = "Working"

	task.append("time_log", {
		"type": "Started",
		"from_time": get_datetime(),
	})

	task.save()

	update_ins_pm(task, status="Working")
	return "Task Started"

@frappe.whitelist()
def pause_task(task_name, reason=None):
	task = frappe.get_doc("Task", task_name)
	task.status = "Paused"
	reason_ = f"Pause Reason: {reason}"
	if task.pause_resume_reason:
		task.pause_resume_reason = str(task.pause_resume_reason) + "\n" + reason_
	else:
		task.pause_resume_reason = reason_

	task.time_log[-1].to_time = get_datetime() 

	task.append("time_log", {
		"type": "Paused",
		"from_time": get_datetime(),
		"reason": reason
	})

	task.save()

	update_ins_pm(task, status="Paused")
	return "Task Paused"

@frappe.whitelist()
def resume_task(task_name, reason=None):
	task = frappe.get_doc("Task", task_name)
	task.status = "Working"
	reason_ = f"Resume Reason: {reason}"
	task.pause_resume_reason = task.pause_resume_reason + "\n" + reason_

	task.time_log[-1].to_time = get_datetime() 

	task.append("time_log", {
		"type": "Resumed",
		"from_time": get_datetime(),
		"reason": reason
	})

	task.save()

	update_ins_pm(task, status="Working")
	return "Task Resumed"

@frappe.whitelist()
def complete_task(task_name):
	task = frappe.get_doc("Task", task_name)
	task.status = "Completed"
	task.completed_on = today()
	task.completed_by = frappe.session.user
	task.time_log[-1].to_time = get_datetime() 

	task.save()

	update_ins_pm(task, status="Completed")


@frappe.whitelist()
def create_replacement_task(doc, description, supervisor=None):
	doc = frappe.parse_json(doc)
	task = frappe.get_doc(
		{
			"doctype": "Task",
			"subject": "Rectification: " + doc.asset_name,
			"project": doc.project,
			"description": description,
			"schedule_cabinet": doc.schedule_cabinet,
			"ins_imp_request": doc.ins_imp_request,
			"asset_unit": doc.asset_unit,
			"parent_task": doc.name,
			"supervisor": supervisor,
		}
	).insert(ignore_permissions=True)
	return task.as_dict()
	
	
def assign_task_to_team(doc, method=None):
	"""
		Assign the task to supervisor if it's subtask assigned to Supervisor, supervisor also can change the team
	"""
	users = []
	if doc.schedule_cabinet and doc.parent_task and not doc.supervisor:
		users = frappe.db.get_all(
			"Team Member", 
			{
				"parenttype": "Schedule Cabinet", 
				"parent": doc.schedule_cabinet
			},
			pluck="user_id"
		)

	if doc.supervisor:
		users = [doc.supervisor]

	if not users:
		return

	args = {
		"assign_to": users,
		"doctype": doc.doctype,
		"name": doc.name,
		"description": doc.description or doc.subject,
	}
	add(args)
	
	for user in users:
		frappe.share.add(doc.doctype, doc.name, user, read=1, write=1, share=1, notify=0)


def calculate_total_time(doc, method=None):
	if not doc.time_log:
		return

	total_time_taken = 0
	for row in doc.time_log:
		total_seconds = time_diff_in_seconds(row.to_time, row.from_time)
		row.time_taken = total_seconds / 60

		if row.type in ["Started", "Resumed"]:
			total_time_taken += row.time_taken

	doc.db_set("total_time_taken", total_time_taken)


@frappe.whitelist()
def get_supervisors(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		SELECT DISTINCT user.name, user.full_name
		FROM `tabUser` user
		JOIN `tabHas Role` role ON user.name = role.parent
		WHERE role.role = 'Supervisor' 
		AND user.enabled = 1
		AND (user.name LIKE %(txt)s OR user.full_name LIKE %(txt)s)
		LIMIT %(start)s, %(page_len)s
	""", {
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len
	})


def change_team_assignment(doc, method=None):
	"""
	This function updates the team assignment in a Task.
	- Removes existing assigned users.
	- Assigns new users from the updated team.
	"""
	if not doc.supervisor or doc.is_new():
		return

	if not doc.is_new():
		update_ins_pm(doc, status="Working") # for changing the team in PM, if supervisor changed the team

	prev_team = frappe.db.get_value('Task', doc.name, 'team')

	if prev_team != doc.team:
		# Remove existing assignments
		frappe.db.delete("ToDo", {"reference_type": "Task", "reference_name": doc.name})

		# Get new team members
		users = frappe.db.get_all(
			"Team Member",
			filters={"parenttype": "Team", "parent": doc.team},
			pluck="user_id"
		)

		# Assign new users to the Task
		args = {
			"assign_to": users,
			"doctype": doc.doctype,
			"name": doc.name,
			"description": doc.description or doc.subject,
		}
		add(args)


def update_task_details(doc, method=None):
	if doc.reference_type != "Task":
		return

	emp_name, phone = frappe.db.get_value(
		"Employee", {"user_id": doc.allocated_to}, ["employee_name", "cell_number"]
	)

	task_details = frappe.db.get_value(
		"Task", 
		doc.reference_name, 
		[
			"posting_date", 
			"team", 
			"schedule_cabinet", 
			"asset_unit", 
			"supervisor",
			"project",
		],
		as_dict=1
	)

	if not task_details or not task_details.get("team"):
		return

	crew_members = frappe.db.get_all(
		"Team Member",
		filters={"parenttype": "Team", "parent": task_details.team},
		pluck="member_name"
	)
	crew = ", ".join(crew_members)

	doc.employee_name = emp_name
	doc.phone_number = phone
	doc.posting_date = task_details.posting_date
	doc.team = task_details.team
	doc.schedule_cabinet = task_details.schedule_cabinet
	doc.asset_unit = task_details.asset_unit
	doc.project = task_details.project
	doc.supervisor = task_details.supervisor
	doc.crew = crew

	# in some scenarios the project is null
	doc.db_set("project", task_details.project)
	if not doc.project:
		doc.db_set("project", frappe.db.get_value("Asset Unit", doc.asset_unit, "project"))

	base_url = "https://ttgqatar.tecizasolutions.com"
	doc.task_url = f"{base_url}/app/task/{doc.reference_name}"

	doc.save()


def update_preventive_maintenance(doc, method=None):
	if doc.status == "Completed" and doc.completed_on:
		update_ins_pm(doc, "Completed")

	if doc.status == "Cancelled":
		update_ins_pm(doc, "Cancelled")


@frappe.whitelist()
def reassign_task(task, new_team):
	doc = frappe.get_doc("Task", task)
	doc.team = new_team
	# Remove existing assignments
	frappe.db.delete("ToDo", {"reference_type": "Task", "reference_name": doc.name})

	# Get new team members
	users = frappe.db.get_all(
		"Team Member",
		filters={"parenttype": "Team", "parent": new_team},
		pluck="user_id"
	)

	# Assign new users to the Task
	args = {
		"assign_to": users,
		"doctype": doc.doctype,
		"name": doc.name,
		"description": doc.description or doc.subject,
	}
	add(args)

	doc.save()


@frappe.whitelist()
def change_incident(task, incident_type, incident_category):
	doc = frappe.get_doc("Task", task)
	doc.incident_type = incident_type
	doc.incident_category = incident_category

	doc.save()

	existing_cm = frappe.db.get_value(
		"Corrective Maintenance", 
		{
			"cm_request": doc.cm_request, 
			"asset_unit": doc.asset_unit, 
			"replacement": 1 if doc.supervisor else 0,
			"docstatus": ["<", 2],
		},
		"name",
	)

	if existing_cm:
		frappe.db.set_value(
			"Corrective Maintenance", 
			existing_cm, 
			{"incident_type": incident_type, "incident_category": incident_category}
		)
