// Copyright (c) 2025, Teciza Solutions and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Department Wise Salary"] = {
	method: "traffictech.traffictech.dashboard_chart_source.department_wise_salary.department_wise_salary.get",
	filters: [
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: ["This Month", "Last Month"],
			default: "Last Month",
		},
	],
};