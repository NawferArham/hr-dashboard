# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dashboard import cache_source
from frappe.query_builder.functions import Sum
from frappe.utils import get_first_day, get_last_day, nowdate, add_months


@frappe.whitelist()
@cache_source
def get(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters={},
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	filters = frappe.parse_json(filters)
	salary_strc = frappe.qb.DocType("Salary Structure Assignment")
	today = nowdate()

	# # Determine month based on filter
	# if filters.get("month") == "This Month":
	# 	from_date = get_first_day(today)
	# 	to_date = get_last_day(today)
	# else:  # Default to Last month
	from_date = get_first_day(add_months(today, -1))
	to_date = get_last_day(add_months(today, -1))

	# Query Salary Structure totals grouped by department
	slips = (
		frappe.qb.from_(salary_strc)
		.select(
			salary_strc.department,
			Sum(salary_strc.custom_total).as_("total_salary")
		)
		.where(
			(salary_strc.docstatus == 1)
			# (salary_slip.start_date >= from_date) &
			# (salary_slip.end_date <= to_date)
		)
		.groupby(salary_strc.department)
	).run(as_dict=True)

	labels = []
	datapoints = []

	for row in slips:
		if row.department:
			labels.append(row.department)
			datapoints.append(row.total_salary)

	return {
		"labels": labels,
		"datasets": [{
			"name": _("Total Salary"),
			"values": datapoints
		}],
		"type": "bar",
	}