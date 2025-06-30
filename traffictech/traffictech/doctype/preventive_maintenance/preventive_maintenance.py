# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, get_datetime, flt
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import zipfile
from io import BytesIO
from frappe.utils.pdf import get_pdf
from frappe import _
import base64
import os
import uuid
from frappe.utils.file_manager import get_file_path
import json
from frappe.utils.xlsxutils import make_xlsx
from frappe.utils.file_manager import save_file


class PreventiveMaintenance(Document):
	def autoname(self):
		if self.replacement:
			self.name = make_autoname(f"REPL-PM-{self.schedule_cabinet}-.####")
		else:
			self.name = make_autoname(f"PM-{self.schedule_cabinet}-.####")

	def validate(self):
		self.vaidate_attachments()

	def vaidate_attachments(self):
		if len(self.before) > 4 or len(self.during) > 4 or len(self.after) > 4:
			frappe.throw("Cannot Attach more than 4 Images, remove the last added row!")

	@frappe.whitelist()
	def create_checklist(self):
		new_checklist = frappe.new_doc("Maintenance Checklist")
		new_checklist.preventive_maintenance = self.name
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


def update_preventive_maintenance(task, status):
	existing_pm = frappe.db.get_value(
		"Preventive Maintenance", 
		{
			"schedule_cabinet": task.schedule_cabinet, 
			"asset_unit": task.asset_unit, 
			"replacement": 1 if task.supervisor else 0,
			"docstatus": ["<", 2],
			# "date": task.posting_date,
		},
		["name", "docstatus", "team"],
		as_dict=1
	)
	
	if existing_pm and existing_pm.docstatus == 1:
		tasks = frappe.db.get_all(
			"Task", 
			{"schedule_cabinet": task.schedule_cabinet, "asset_unit": task.asset_unit, "team": task.team}, 
			["name", "total_time_taken"]
		)
		total_time = 0
		for task_ in tasks:
			total_time += flt(task_.total_time_taken)

		frappe.db.set_value("Preventive Maintenance", existing_pm.name, {
				"total_time_taken": total_time,
				"status": status,
				"completed_date": task.completed_on,
			}
		)

		return

	if existing_pm:
		pm = frappe.get_doc("Preventive Maintenance", existing_pm.name)
		pm.status = status

		# add team members
		if pm.team != task.team:
			pm.team = task.team
			pm.team_members = []
			team_members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": task.team},
				["member", "engineer_in_charge"]
			)
			for mem in team_members:
				pm.append("team_members", {
					"member": mem.member,
					"engineer_in_charge": mem.engineer_in_charge,
				})

		# add tasks
		pm.tasks = []
		tasks = frappe.db.get_all(
			"Task", 
			{"schedule_cabinet": task.schedule_cabinet, "asset_unit": task.asset_unit, "team": pm.team}, 
			["name", "total_time_taken"]
		)
		total_time = 0
		for task_ in tasks:
			pm.append("tasks", {
				"task": task_.name
			})
			total_time += flt(task_.total_time_taken)

		pm.total_time_taken = total_time

		if task.completed_on:
			pm.completed_date = task.completed_on

		pm.save()
	else:
		pm = frappe.get_doc({
			"doctype": "Preventive Maintenance",
			"date": today(),
			"schedule_cabinet": task.schedule_cabinet,
			"asset_unit": task.asset_unit,
			"start_time": get_datetime(),
			"end_time": "",
			"total_time_taken": "",
			"status": status,
			"replacement": 1 if task.supervisor else 0,
			"team": task.team,
		})

		team_members = frappe.db.get_all(
			"Team Member",
			{"parenttype": "Team", "parent": task.team},
			["member", "engineer_in_charge"]
		)

		if pm.replacement:
			team_members = frappe.db.get_all(
				"Team Member",
				{"parenttype": "Team", "parent": task.team},
				["member", "engineer_in_charge"]
			)

		for mem in team_members:
			pm.append("team_members", {
				"member": mem.member,
				"engineer_in_charge": mem.engineer_in_charge,
			})

		tasks = frappe.db.get_all(
			"Task", 
			{"schedule_cabinet": task.schedule_cabinet, "asset_unit": task.asset_unit}, 
			pluck="name"
		)
		for task in tasks:
			pm.append("tasks", {
				"task": task
			})

		pm.insert(ignore_permissions=True)
		pm.save()


@frappe.whitelist()
def download_reports(reports):
	if isinstance(reports, str):
		reports = json.loads(reports)
	if not reports:
		frappe.throw(_("No reports selected."))

	buffer = BytesIO()
	with zipfile.ZipFile(buffer, 'w') as zipf:
		for name in reports:
			doc = frappe.get_doc("Preventive Maintenance", name)
			asset_unit = frappe.db.get_value(
				"Asset Unit", 
				doc.asset_unit, 
				["asset_id", "asset_name", "junction_no"], 
				as_dict=1
			)
			pdf_file = frappe.get_print(
				"Preventive Maintenance",
				name,
				doc=doc,
			)

			file_name = f"{asset_unit.asset_name}-{asset_unit.junction_no}.pdf"
			if asset_unit.asset_id:
				file_name = f"{asset_unit.asset_id}-{asset_unit.asset_name}-{asset_unit.junction_no}.pdf"

			pdf = get_pdf(pdf_file)
			zipf.writestr(file_name, pdf)

	buffer.seek(0)

	frappe.local.response.filename = "Preventive_Maintenance_Reports.zip"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "binary"


@frappe.whitelist()
def download_comments(pm):
	import io

	if isinstance(pm, str):
		pm = json.loads(pm)

	if not pm:
		frappe.throw(_("No Maintenance selected."))

	cache_key = f"export_comments_{frappe.session.user}_{uuid.uuid4().hex}"

	frappe.enqueue(
		method="traffictech.traffictech.doctype.preventive_maintenance.preventive_maintenance.enqueue_comments_export",
		queue="long",
		pm=pm,
		user=frappe.session.user,
		cache_key=cache_key
	)

	return _("Export started. You’ll be notified when ready.")


def enqueue_comments_export(pm, user=None, cache_key=None):
	"""Enqueue the export of comments for the given Preventive Maintenance records."""
	data = [["Preventive Maintenance Comments"]]

	PM = frappe.qb.DocType("Preventive Maintenance")
	PMComment = frappe.qb.DocType("Preventive Maintenance Comment")
	Checklist = frappe.qb.DocType("Maintenance Checklist")
	ChecklistActivity = frappe.qb.DocType("Maintenance Checklist Template Activity")

	results = (
		frappe.qb.from_(PM)
		.left_join(PMComment).on((PM.name == PMComment.parent) & (PMComment.comment != ""))
		.left_join(Checklist).on(PM.name == Checklist.preventive_maintenance)
		.left_join(ChecklistActivity)
		.on((Checklist.name == ChecklistActivity.parent) & (ChecklistActivity.divider == 1) & (ChecklistActivity.comments != ""))
		.select(
			PM.name.as_("pm_id"),
			PM.asset_unit,
			PM.asset_name,
			PMComment.comment.as_("pm_comment"),
			ChecklistActivity.comments.as_("chk_comment")
		)
		.where(
			(PM.name.isin(pm))
		)
		.run(as_dict=True)
	)

	grouped = frappe._dict()
	for row in results:
		key = (row.pm_id, row.asset_unit, row.asset_name)
		entry = grouped.setdefault(key, {"pm_comments": set(), "chk_comments": set()})
		entry["pm_comments"].add(row.pm_comment)
		entry["chk_comments"].add(row.chk_comment)

	for (pm_id, asset_unit, asset_name), comments in grouped.items():
		if comments["pm_comments"] == {None} and comments["chk_comments"] == {None}:
			continue

		data.append([f"ID - {pm_id}", f"Asset Unit - {asset_unit}", f"Asset Name - {asset_name}"])

		data.append(["PM Comments:"])
		for pm_comment in comments["pm_comments"]:
			data.append([pm_comment])

		data.append(["Checklist Comments:"])
		for chk_comment in comments["chk_comments"]:
			data.append([chk_comment])

		data.append([])

	xlsx_file = make_xlsx(data, "Preventive Maintenance Comments")

	# Store in Redis (with TTL of 5 mins)
	frappe.cache().set_value(cache_key, xlsx_file.getvalue(), expires_in_sec=300)

	# Notify user with link
	download_url = f"/api/method/traffictech.traffictech.doctype.preventive_maintenance.preventive_maintenance.download_cached_file?key={cache_key}"

	frappe.publish_realtime(
		event="comments_export_complete",
		message={"download_url": download_url},
		user=user
	)


@frappe.whitelist()
def download_cached_file(key):
	filecontent = frappe.cache().get_value(key)
	if not filecontent:
		frappe.throw(_("File not found or already downloaded."), title="Download Expired")

	# Clear it immediately after access
	frappe.cache().delete_value(key)

	frappe.local.response.filename = "comments_export.xlsx"
	frappe.local.response.filecontent = filecontent
	frappe.local.response.type = "binary"
	frappe.local.response.charset = "utf-8"