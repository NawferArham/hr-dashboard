# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.background_jobs import enqueue, is_job_enqueued
from frappe.core.doctype.data_import.data_import import DataImport
from .importer import CustomImporter


class CustomDataImport(DataImport):
	def start_import(self):
		from frappe.utils.scheduler import is_scheduler_inactive

		run_now = frappe.flags.in_test or frappe.conf.developer_mode
		if is_scheduler_inactive() and not run_now:
			frappe.throw(_("Scheduler is inactive. Cannot import data."), title=_("Scheduler Inactive"))

		job_id = f"data_import||{self.name}"

		if not is_job_enqueued(job_id):
			enqueue(
				start_import,
				queue="default",
				timeout=10000,
				event="data_import",
				job_id=job_id,
				data_import=self.name,
				now=run_now,
			)
			return True

		return False


def start_import(data_import):
	"""This method runs in background job"""
	data_import = frappe.get_doc("Data Import", data_import)
	try:
		i = CustomImporter(data_import.reference_doctype, data_import=data_import)
		i.import_data()
	except JobTimeoutException:
		frappe.db.rollback()
		data_import.db_set("status", "Timed Out")
	except Exception:
		frappe.db.rollback()
		data_import.db_set("status", "Error")
		data_import.log_error("Data import failed")
	finally:
		frappe.flags.in_import = False

	frappe.publish_realtime("data_import_refresh", {"data_import": data_import.name})