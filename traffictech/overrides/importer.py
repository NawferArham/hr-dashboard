# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.core.doctype.data_import.importer import Importer, get_id_field
from frappe.core.doctype.version.version import get_diff


INSERT = "Insert New Records"
UPDATE = "Update Existing Records"
INSERT_AND_UPDATE = "Insert and Update Existing Records"


class CustomImporter(Importer):
	def process_doc(self, doc):
		if self.import_type == INSERT:
			return self.insert_record(doc)
		elif self.import_type == UPDATE:
			return self.update_record(doc)
		elif self.import_type == INSERT_AND_UPDATE:
			return self.insert_and_update_record(doc)

	def insert_and_update_record(self, doc):
		id_field = get_id_field(self.doctype)
		
		if not doc.get(id_field.fieldname):
			return self.insert_record(doc)

		existing_doc = frappe.db.exists(self.doctype, doc.get(id_field.fieldname))
		if not existing_doc:
			return self.insert_record(doc)

		existing_doc = frappe.get_doc(self.doctype, doc.get(id_field.fieldname))
		updated_doc = frappe.get_doc(self.doctype, doc.get(id_field.fieldname))

		updated_doc.update(doc)

		if get_diff(existing_doc, updated_doc):
			# update doc if there are changes
			updated_doc.flags.updater_reference = {
				"doctype": self.data_import.doctype,
				"docname": self.data_import.name,
				"label": _("via Data Import"),
			}
			updated_doc.save()
			return updated_doc
		else:
			# throw if no changes
			frappe.msgprint(_("No changes to update"))
