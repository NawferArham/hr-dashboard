// Copyright (c) 2025, Teciza Solutions and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Employee In Out"] = {
	method: "traffictech.traffictech.dashboard_chart_source.employee_in_out.employee_in_out.get",
	filters: [
	],
};