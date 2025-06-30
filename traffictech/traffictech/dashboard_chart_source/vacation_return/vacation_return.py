# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dashboard import cache_source
from frappe.query_builder.functions import Count
from frappe.utils import today, flt


@frappe.whitelist()
@cache_source
def get(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	filters = frappe.parse_json(filters)

	lv_ap = frappe.qb.DocType("Leave Application Form")

	# Get approved, active leave applications for "Annual Paid Leave"
	leave_data = (
		frappe.qb.from_(lv_ap)
		.select(
			lv_ap.leave_end_date,
			Count(lv_ap.employee_code).as_("count")
		)
		.where(
			(lv_ap.docstatus == 1) &
			(lv_ap.leave_type == "Annual Paid Leave") &
			(lv_ap.leave_end_date >= today())
		)
		.groupby(lv_ap.leave_end_date)
	).run(as_dict=True)

	# Prepare chart data
	labels = []
	datapoints = []
	colors = []

	color_palette = [
		"#5E64FF", "#743EE2", "#FF5858", "#FFBF00",
		"#00B0F0", "#00A991", "#FFA3EF", "#FFC148"
	]

	for row in sorted(leave_data, key=lambda x: x["leave_end_date"]):
		labels.append(str(row["leave_end_date"]))
		datapoints.append(row["count"])
		colors.append(color_palette[row["count"] % len(color_palette)])

	return {
		"labels": labels,
		"datasets": [{
			"name": _("Employees Returning"),
			"values": datapoints
		}],
		"type": "bar",
		"colors": colors
	}