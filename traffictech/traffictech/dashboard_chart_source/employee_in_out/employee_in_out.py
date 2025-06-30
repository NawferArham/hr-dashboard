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
	labels, datapoints = [], []
	filters = frappe.parse_json(filters)

	emp_chkin = frappe.qb.DocType("Employee Checkin")

	result = (
		frappe.qb.from_(emp_chkin)
		.select(
			Count(emp_chkin.log_type).as_("count"),
			emp_chkin.log_type
		)
		.groupby(emp_chkin.log_type)
		.where(Date(emp_chkin.time) == today())
	)

	type_wise = {}
	result = result.run(as_dict=1)
	for res in result:
		labels.append(_(res.get("log_type")))
		datapoints.append(res.get("count"))


	return {
		"labels": labels,
		"datasets": [{"name": _("Attendance"), "values": datapoints}],
		"type": "donut",
	}