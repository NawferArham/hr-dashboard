# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	# for hiding the sales_stage and probability in opportunity: there is custom pipeline for this.
	setters = [
		{
			"doctype":"Opportunity",
			"fieldname":"sales_stage",
			"property":"hidden",
			"value":1,
			"property_type":"Check",
		},
		{
			"doctype":"Opportunity",
			"fieldname":"probability",
			"property":"default",
			"value":0,
			"property_type":"Small Text",
		}
	]

	for row in setters:
		make_property_setter(
			doctype=row["doctype"],
			fieldname=row["fieldname"],
			property=row["property"],
			value=row["value"],
			property_type=row["property_type"],
		)

	create_custom_fields(
		{
			"Opportunity": [
				{
					"fieldname": "crm_pipeline",
					"fieldtype": "Link",
					"label": "Pipeline",
					"options": "CRM Pipeline",
					"insert_after": "opportunity_type",
					"reqd": 1,
				},
				{
					"fieldname": "opportunity_stage",
					"fieldtype": "Link",
					"label": "Opportunity Stage",
					"options": "Opportunity Stage",
					"insert_after": "sales_stage",
				},
			],
			"Customer": [
				{
					"label": "Activities",
					"fieldname": "activity_tab",
					"fieldtype": "Tab Break",
					"insert_after": "portal_users",
				},
				{
					"fieldname": "open_activities_html",
					"fieldtype": "HTML",
					"label": "Open Activities HTML",
					"insert_after": "activity_tab",
				},
				{
					"label": "All Activities",
					"fieldname": "section_all_activity",
					"fieldtype": "Section Break",
					"insert_after": "open_activities_html",
				},
				{
					"fieldname": "all_activities_html",
					"fieldtype": "HTML",
					"label": "All Activities HTML",
					"insert_after": "section_all_activity",
				},
			]
		}
	) 