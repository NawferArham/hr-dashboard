// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.query_reports["Expense Register"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "supplier",
			label: __("Suplier"),
			fieldtype: "Data",
		},
		{
			fieldname: "show_summary",
			label: __("Show Summary"),
			fieldtype: "Check",
			default: 0,
		},
	]
};
