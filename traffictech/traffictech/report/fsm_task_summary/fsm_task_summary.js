// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.query_reports["FSM Task Summary"] = {
	"filters": [
		{
			"fieldname": "fiscal_year",
			"label": "Fiscal Year",
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd": 1,
			"default": erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
		},
		{
			"fieldname": "month",
			"label": "Month",
			"fieldtype": "Select",
			"options": "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
			// "reqd": 1
		},
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname": "show_per_day",
			"label": "Show Per Day",
			"fieldtype": "Check",
			"default": 0
		}
	]
};
