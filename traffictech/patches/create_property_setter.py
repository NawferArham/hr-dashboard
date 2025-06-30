# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	make_property_setter(
		"Task",
		"status",
		"options",
		"Open\nWorking\nPaused\nPending Review\nOverdue\nManually Done\nTemplate\nCompleted\nCancelled\nRejected",
		"Small Text",
	)

	make_property_setter(
		"Data Import",
		"import_type",
		"options",
		"\nInsert New Records\nUpdate Existing Records\nInsert and Update Existing Records",
		"Small Text",
	)