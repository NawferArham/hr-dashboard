# Copyright (c) 2025, Teciza and contributors
# For license information, please see license.txt

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Quotation Item": [
				{
					"fieldname": "group",
					"fieldtype": "Data",
					"label": "Group",
					"insert_after": "against_blanket_order",
					"read_only": 1,
				},
				{
					"fieldname": "clm_break",
					"fieldtype": "Column Break",
					"insert_after": "group",
				},
				{
					"fieldname": "estimation",
					"fieldtype": "Link",
					"label": "Estimation",
					"options": "Estimation",
					"insert_after": "clm_break",
					"read_only": 1,
				},
				{
					"fieldname": "estimation_item",
					"fieldtype": "Data",
					"label": "Estimation Item",
					"insert_after": "estimation",
					"read_only": 1,
				},
			],
			"Quotation": [
				{
					"fieldname": "sales_person",
					"fieldtype": "Link",
					"options": "Sales Person",
					"label": "Sales Person",
					"insert_after": "valid_till",
				},
				{
					"fieldname": "print_with_tax",
					"fieldtype": "Check",
					"label": "Print with Tax",
					"insert_after": "company",
					"allow_on_submit": 1,
					"depends_on": "eval: doc.docstatus == 1;",
				},
				{
					"fieldname": "print_with_remarks",
					"fieldtype": "Check",
					"label": "Print with Remarks",
					"insert_after": "print_with_tax",
					"allow_on_submit": 1,
					"depends_on": "eval: doc.docstatus == 1;",
				},
				{
					"fieldname": "print_only_qty",
					"fieldtype": "Check",
					"label": "Print only with Qty",
					"insert_after": "print_with_remarks",
					"allow_on_submit": 1,
					"depends_on": "eval: doc.docstatus == 1;",
				},
				{
					"fieldname": "notes_section",
					"fieldtype": "Section Break",
					"label": "Notes",
					"insert_after": "terms",
				},
				{
					"fieldname": "notes",
					"fieldtype": "Text Editor",
					"insert_after": "notes_section",
				},
				{
					"fieldname": "subject",
					"label": "Subject",
					"fieldtype": "Data",
					"insert_after": "order_type",
				},
			]
		}
  	)