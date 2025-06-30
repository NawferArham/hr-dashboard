// Copyright (c) 2025, Teciza Solutions and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Document Expiry Details"] = {
	method: "traffictech.traffictech.dashboard_chart_source.document_expiry_details.document_expiry_details.get",
	filters: [
	],
};