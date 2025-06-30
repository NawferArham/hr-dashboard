# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, get_first_day, get_last_day, formatdate, add_days, flt
from collections import defaultdict

def execute(filters=None):
	columns = get_columns()
	data, tasks = get_summary_data(filters)
	chart = get_chart_data(filters, tasks)
	
	return columns, data, None, chart

def get_columns():
	return [
		{"label": "", "fieldname": "metric", "fieldtype": "Data", "width": 300},
		{"label": "", "fieldname": "value", "fieldtype": "Data", "width": 300},
	]

def get_summary_data(filters):
	task_wise = {}
	per_day = {}

	fiscal_year = filters.get("fiscal_year")
	project = filters.get("project")
	month = filters.get("month")

	# Get fiscal year starting year
	year_start_date, year_end_date = frappe.get_value(
		"Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"]
	)
	fiscal_start_year = getdate(year_start_date).year

	conditions = f"""
		YEAR(posting_date) = {fiscal_start_year}
		AND month != ''
	"""
	if month:
		conditions += f"AND month = '{month}'"

	if project:
		conditions += f" AND project = '{project}'"

	tasks = frappe.db.sql(f"""
		SELECT 
			name,
			status,
			completed_on,
			posting_date,
			month
		FROM `tabTask`
		WHERE {conditions}
	""", as_dict=True)

	for task in tasks:
		task_wise.setdefault(task.status, 0)
		task_wise[task.status] += 1

		if task.status == "Completed" and task.completed_on:
			date_str = formatdate(task.completed_on, "dd-mm-yyyy")
			per_day[date_str] = per_day.get(date_str, 0) + 1

	if not len(tasks):
		frappe.throw("No Tasks Scheduled")

	total_tasks = len(tasks)
	completed_tasks = flt(task_wise.get("Completed"))
	working_tasks = flt(task_wise.get("Working"))
	paused_tasks = flt(task_wise.get("Paused"))
	cancelled_tasks = flt(task_wise.get("Cancelled"))
	open_tasks = flt(task_wise.get("Open"))
	manually_done = flt(task_wise.get("Manually Done"))

	summary_data = [
		{"metric": "Total Tasks", "value": str(total_tasks)},
		{"metric": "Completed Tasks", "value": f"{completed_tasks} ({completed_tasks/total_tasks*100:.1f}%)"},
		{"metric": "Working Tasks", "value": f"{working_tasks}/{total_tasks} ({working_tasks/total_tasks*100:.1f}%)"},
		{"metric": "Manually Done", "value": f"{manually_done}/{total_tasks} ({manually_done/total_tasks*100:.1f}%)"},
		{"metric": "Paused Tasks", "value": f"{paused_tasks} ({paused_tasks/total_tasks*100:.1f}%)"},
		{"metric": "Open Tasks", "value": f"{open_tasks} ({open_tasks/total_tasks*100:.1f}%)"},
		{"metric": "Cancelled Tasks", "value": f"{cancelled_tasks} ({cancelled_tasks/total_tasks*100:.1f}%)"}
	]

	if filters.get("show_per_day"):			
		# Sort by date
		for date in sorted(per_day.keys()):
			summary_data.append({
				"metric": date,
				"value": str(per_day[date])
			})
	
	return summary_data, tasks

def get_month_date_range(fiscal_year, month_name):
	year_start_date, year_end_date = frappe.get_value(
		"Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"]
	)
	fy_start = getdate(year_start_date)
	year = fy_start.year

	months = [
		'', 'January', 'February', 'March', 'April', 'May', 'June',
		'July', 'August', 'September', 'October', 'November', 'December'
	]

	index = months.index(month_name) if month_name else 1

	start_date = get_first_day(f"{year}-{index:02d}-01") if month_name else year_start_date
	end_date = get_last_day(start_date) if month_name else year_end_date

	return start_date, end_date

def get_chart_data(filters, tasks):
	# Group by week or month and status
	groupwise_data = defaultdict(lambda: defaultdict(int))
	statuses = ["Open", "Working", "Completed", "Paused", "Cancelled"]
	month_names = [
		"", "January", "February", "March", "April", "May", "June",
		"July", "August", "September", "October", "November", "December"
	]

	if filters.get("month"):
		# If month selected → group by week
		for task in tasks:
			if task.get("posting_date"):
				date_obj = getdate(task["posting_date"])
				week_number = (date_obj.day - 1) // 7 + 1
				group_key = f"Week {week_number}"
				groupwise_data[group_key][task["status"]] += 1
	else:
		for task in tasks:
			if task.get("month"):
				groupwise_data[task.month][task["status"]] += 1

	if filters.get("month"):
		groups = sorted(groupwise_data.keys(), key=lambda x: int(x.split(' ')[1]))  # Week 1, Week 2 etc.
	else:
		groups = month_names[1:]  # Full January to December

	datasets = []
	colors = ["#ff6384", "#36a2eb", "#4bc0c0", "#ffcd56", "#9966ff"]  # Different color for each status

	for i, status in enumerate(statuses):
		values = [groupwise_data[g].get(status, 0) for g in groups]
		datasets.append({
			"name": status,
			"values": values,
			"chartType": "bar",
			"color": colors[i]
		})

	chart = {
		"data": {
			"labels": groups,
			"datasets": datasets
		},
		"type": "bar",
		"barOptions": {
			"stacked": True
		},
		"height": 300,
		"colors": colors,
		"title": "Task Status Breakdown"
	}

	return chart