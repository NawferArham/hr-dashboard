// Copyright (c) 2025, Teciza Solutions and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Employee In Outside Country"] = {
	method: "traffictech.traffictech.dashboard_chart_source.employee_in_outside_country.employee_in_outside_country.get",
	filters: [
	],
};