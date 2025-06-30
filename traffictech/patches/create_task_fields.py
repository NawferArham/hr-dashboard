# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Task": [
				{
					"fieldname": "cancel_reason",
					"fieldtype": "Small Text",
					"label": "Cancel Reason",
					"insert_after": "pause_resume_reason",
					"depends_on": "eval: doc.status == 'Cancelled';",
					"mandatory_depends_on": "eval: doc.status == 'Cancelled';",
				},
				{
					"fieldname": "ins_imp_request",
					"fieldtype": "Link",
					"options": "Inspection Improvement Request",
					"label": "Inspection Improvement Request",
					"insert_after": "cabinet_section",
					"read_only": 1
				},
				{
					"fieldname": "fiscal_year",
					"fieldtype": "Link",
					"options": "Fiscal Year",
					"label": "Fiscal Year",
					"insert_after": "posting_date",
					"read_only": 1,
					"fetch_from": "schedule_cabinet.fiscal_year",
				},
				{
					"fieldname": "month",
					"fieldtype": "Select",
					"options": "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
					"label": "Month",
					"insert_after": "fiscal_year",
					"read_only": 1,
					"fetch_from": "schedule_cabinet.month",
				},
				{
					"fieldname": "cm_request",
					"fieldtype": "Link",
					"options": "Corrective Maintenance Request",
					"label": "Corrective Maintenance Request",
					"insert_after": "ins_imp_request",
					"read_only": 1
				},
				{
					"fieldname": "incident_type",
					"fieldtype": "Link",
					"options": "Incident",
					"label": "Incident Type",
					"insert_after": "rectification_required",
					# "fetch_from": "cm_request.incident_type",
					"read_only": 1
				},
				{
					"fieldname": "incident_category",
					"fieldtype": "Link",
					"options": "Incident",
					"label": "Incident Category",
					"insert_after": "incident_type",
					# "fetch_from": "cm_request.incident_category",
					"read_only": 1
				},
			]
		}
	)