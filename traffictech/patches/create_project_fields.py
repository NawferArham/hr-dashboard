# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Project": [
				{
					"fieldname": "contract_client_details",
					"fieldtype": "Section Break",
					"label": "Contract/Client Details",
					"insert_after": "footer_for_report",
				},
				{
					"fieldname": "contractor",
					"fieldtype": "Data",
					"label": "Contractor",
					"insert_after": "contract_client_details",
				},
				{
					"fieldname": "contract_no",
					"fieldtype": "Data",
					"label": "Contract No",
					"insert_after": "contractor",
				},
				{
					"fieldname": "contractor_representative",
					"fieldtype": "Data",
					"label": "Contractor Representative",
					"insert_after": "contract_no",
				},
				{
					"fieldname": "contractor_scope_ref",
					"fieldtype": "Data",
					"label": "Contractor Scope Reference",
					"insert_after": "contractor_representative",
				},
				{
					"fieldname": "client_clm_break",
					"fieldtype": "Column Break",
					"insert_after": "contractor_scope_ref",
				},
				{
					"fieldname": "client",
					"fieldtype": "Data",
					"label": "Client",
					"insert_after": "client_clm_break",
				},
				{
					"fieldname": "client_representative",
					"fieldtype": "Data",
					"label": "Client Representative",
					"insert_after": "client",
				},
				
			]
		}
	)