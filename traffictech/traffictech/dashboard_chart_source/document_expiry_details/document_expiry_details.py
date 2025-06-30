# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.dashboard import cache_source
from frappe.query_builder.functions import Sum
from frappe.utils import get_first_day, get_last_day, nowdate, add_months, today, get_month
from erpnext.accounts.utils import get_fiscal_year


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
	report = frappe.get_doc("Report", "Document Expiry Details")
	filters = {
		"year": get_fiscal_year(today(), as_dict=True).get("name") or  "2025",
		"month": get_month(),
		"status": "Expired",
	}
	columns, data = report.get_data(
		user=frappe.session.user,
		filters=filters,
		as_dict=True,
		ignore_prepared_report=True,
	)

	docs = ["QID", "Passport", "Health Card"]
	doc_wise = {}
	for row in data:
		if row.document in docs:
			doc_wise.setdefault(row.document, [])
			doc_wise[row.document].append(row.employee_name)

	labels = []
	datapoints = []

	for doc, emp in doc_wise.items():
		value = len(emp)
		labels.append(doc)
		datapoints.append(value)

	return {
		"labels": labels,
		"datasets": [{
			"name": _("Expiring this Month"),
			"values": datapoints
		}],
		"type": "bar",
	}