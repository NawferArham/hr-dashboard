// Copyright (c) 2025, Teciza Solutions and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Vacation Return"] = {
	method: "traffictech.traffictech.dashboard_chart_source.vacation_return.vacation_return.get",
	filters: [
	],
};