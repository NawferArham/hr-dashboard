// Copyright (c) 2025, Teciza Solutions and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Nationality Wise Employee"] = {
	method: "traffictech.traffictech.dashboard_chart_source.nationality_wise_employee.nationality_wise_employee.get",
	filters: [
	],
};