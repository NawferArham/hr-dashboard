# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dashboard import cache_source
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

	# Get employees currently on approved Annual Paid Leave and not ended yet
	on_leave = (
		frappe.qb.from_(lv_ap)
		.select(lv_ap.employee_code)
		.where(
			(lv_ap.docstatus == 1) &
			(lv_ap.leave_type == "Annual Paid Leave") &
			(lv_ap.leave_end_date >= today())
		)
	).run(as_dict=True)

	leave_emp_codes = set(row["employee_code"] for row in on_leave)

	# Get employees who are back from vacation
	back_from = frappe.qb.DocType("Back From Vacation")

	back_emp = (
		frappe.qb.from_(back_from)
		.select(back_from.employee_code)
		.where(
			(back_from.docstatus == 1) &
			(back_from.date <= today())
		)
	).run(as_dict=True)

	back_emp_codes = set(row["employee_code"] for row in back_emp)


	business= frappe.qb.DocType("Business Trip Request")

	busn_trip = (
		frappe.qb.from_(business)
		.select(business.employee)
		.where(
			(business.to_date >= today())
		)
	).run(as_dict=True)

	busn_trip_emp_codes = set(row["employee"] for row in busn_trip)

	# Employees still on vacation = leave_emp_codes - back_emp_codes
	still_on_vacation = (leave_emp_codes - back_emp_codes) 
	in_vacation = len(still_on_vacation) + len(busn_trip_emp_codes)

	# Total active employees
	total_no_employees = len(
		frappe.db.get_all("Employee", filters={"status": "Active"}, pluck="name")
	)

	labels = []
	datapoints = []

	labels.append(_("In Country"))
	datapoints.append(total_no_employees - in_vacation)

	labels.append(_("Outside Country"))
	datapoints.append(in_vacation)

	labels.append(_("In Vacation"))
	datapoints.append(len(back_emp_codes))

	labels.append(_("Business Trip"))
	datapoints.append(len(busn_trip_emp_codes))

	return {
		"labels": labels,
		"datasets": [{
			"name": _(""),
			"values": datapoints
		}],
		"type": "bar",
	}
