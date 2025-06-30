# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dashboard import cache_source
from frappe.query_builder.functions import Date, Count
from frappe.utils import today


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
	labels, datapoints, colors = [], [], []
	filters = frappe.parse_json(filters)

	emp = frappe.qb.DocType("Employee")

	result = (
		frappe.qb.from_(emp)
		.select(
			Count(emp.custom_nationality).as_("count"),
			emp.custom_nationality
		)
		.groupby(emp.custom_nationality)
		.where(emp.status == "Active")
		.where(emp.custom_nationality != "")
	)

	result = result.run(as_dict=1)
	color_palette = [
		"#5E64FF", "#743EE2", "#FF5858", "#FFBF00",
		"#00B0F0", "#00A991", "#FFA3EF", "#FFC148"
	]

	for i, res in enumerate(result):
		labels.append(_(res.get("custom_nationality")))
		datapoints.append(res.get("count"))
		colors.append(color_palette[i % len(color_palette)])

	return {
		"labels": labels,
		"datasets": [{
			"name": _("Nationality"),
			"values": datapoints
		}],
		"type": "bar",
		"colors": colors
	}