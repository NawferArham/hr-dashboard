import frappe
from frappe.query_builder.functions import Date, Count, Sum, Extract
from frappe.utils import today, get_month, getdate, now_datetime, flt
from calendar import month_name
from frappe import _
from erpnext.accounts.utils import get_fiscal_year
from erpnext import get_default_company
from hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet import execute as execute_monthly_attendance_sheet


@frappe.whitelist()
def get_employee_in_out():
	labels, datapoints = [], []
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
	total_emp = get_total_employee_count(office=True)

	in_ = 0
	out = 0
	for res in result:
		if res.get("log_type") == "IN":
			in_ = res.get("count")
		else:
			out = res.get("count")
	
	labels.append(_("IN"))
	datapoints.append(in_ - out)
		
	labels.append(_("OUT"))
	datapoints.append((total_emp - in_) + out)
	
	return {"labels": labels, "values": datapoints}


@frappe.whitelist()
def get_salary_data(group_by):
	salary_strc = frappe.qb.DocType("Salary Structure Assignment")	
	slips = (
		frappe.qb.from_(salary_strc)
		.select(
			salary_strc[group_by],
			Sum(salary_strc.custom_total).as_("total_salary")
		)
		.where(
			(salary_strc.docstatus == 1)
		)
		.groupby(salary_strc[group_by])
	)

	if group_by == "department":
		dept = frappe.qb.DocType("Department")
		slips = slips.join(dept).on(salary_strc.department == dept.name)
		slips = slips.select(dept.department_name.as_("name"))

	slips = slips.run(as_dict=True)

	labels = []
	datapoints = []

	for row in slips:
		if row.get(group_by):
			labels.append(row.get("name") or row.get(group_by))
			datapoints.append(row.total_salary)

	return {"labels": labels, "values": datapoints}

@frappe.whitelist()
def get_outside_country_data():
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

	return {"labels": labels, "values": datapoints}


@frappe.whitelist()
def get_gender_ratio():
	labels, datapoints = [], []
	emp = frappe.qb.DocType("Employee")

	result = (
		frappe.qb.from_(emp)
		.select(
			Count(emp.gender).as_("count"),
			emp.gender
		)
		.groupby(emp.gender)
		.where(emp.status == "Active")
		.where(emp.gender != "")
	)

	result = result.run(as_dict=1)

	for i, res in enumerate(result):
		labels.append((res.get("gender")))
		datapoints.append(res.get("count"))
	return {"labels": labels, "values": datapoints}


@frappe.whitelist()
def get_job_applicant_details(group_by):
	data = frappe.db.get_all('Job Applicant', 
		fields=[group_by, f'count({group_by}) as count'], 
		group_by=group_by
	)

	appli_wise = {}
	for row in data:
		appli_wise.setdefault(row.get(group_by), row.get("count"))

	return {"labels": list(appli_wise.keys()), "values": list(appli_wise.values())}


@frappe.whitelist()
def get_job_applicant_frequency():
	current_year = getdate().year

	# Fetch job applicants grouped by creation date (monthly) using the 'creation' field
	results = frappe.db.sql("""
		SELECT MONTH(creation) AS month, COUNT(*) AS count
		FROM `tabJob Applicant`
		WHERE YEAR(creation) = %s
		GROUP BY MONTH(creation)
		ORDER BY month ASC
	""", current_year, as_dict=True)

	month_names = [
		"January", "February", "March", "April", "May", "June",
		"July", "August", "September", "October", "November", "December"
	]
	labels = month_names
	values = [0] * 12
	for row in results:
		month_index = row.month - 1
		values[month_index] = row.count

	return {"labels": labels, "values": values}


@frappe.whitelist()
def get_designation_counts():
	data = frappe.db.get_all('Employee', 
		filters={"designation": ["!=", ""]}, 
		fields=["designation", "count('designation') as count"], 
		group_by='designation'
	)
	design_wise = {}
	for row in data:
		design_wise.setdefault(row.get("designation"), row.get("count"))

	return {"labels": list(design_wise.keys()), "values": list(design_wise.values())}


@frappe.whitelist()
def get_job_openings_details(group_by):
	data = frappe.db.get_all('Job Opening', 
		fields=[group_by, f'count({group_by}) as count'],
		filters={"status": "Open"},
		group_by=group_by
	)

	open_wise = {}
	for row in data:
		open_wise.setdefault(row.get(group_by), row.get("count"))

	return {"labels": list(open_wise.keys()), "values": list(open_wise.values())}


@frappe.whitelist()
def get_nationality_counts():
	labels, datapoints, colors = [], [], []
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

	for i, res in enumerate(result):
		labels.append(res.get("custom_nationality"))
		datapoints.append(res.get("count"))

	return {"labels": labels, "values": datapoints}


@frappe.whitelist()
def get_total_salary_structure_amount():
	total = frappe.db.sql("""
		SELECT SUM(custom_total) AS total
		FROM `tabSalary Structure Assignment`
		WHERE docstatus = 1
	""", as_dict=True)

	return total[0].total or 0


def get_total_employee_count(office):
	filters = {
		"status": "Active"
	}
	if office:
		filters["custom_work_location"] = "Head Office"
	count = frappe.db.get_all('Employee', filters, "count('name') as count")
	return count[0].get("count", 0)


@frappe.whitelist()
def get_document_expiry_details():
	report = frappe.get_doc("Report", "Document Expiry Details")
	filters = {
		"year":  "2025",
		# "month": get_month(),
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
		labels.append(doc)
		datapoints.append(len(emp))

	return {"labels": labels, "values": datapoints}


@frappe.whitelist()
def get_attendance_counts():
	filters = {
		"year":  "2025",
		"month": now_datetime().month,
		"company": get_default_company(),
	}

	columns, data, message, chart = execute_monthly_attendance_sheet(filters=filters)
	if not chart:
		return {"labels": [], "values": []}

	chart_data = chart.get("data", {})

	return {"labels": chart_data.get("labels"), "values": chart_data.get("values")}


@frappe.whitelist()
def get_expense_claims(group_by):
	data = frappe.db.get_all('Expense Claim', 
		fields=[group_by, f'count({group_by}) as count'],
		filters={"docstatus": 1},
		group_by=group_by
	)

	expenses = {}
	for row in data:
		expenses.setdefault(row.get(group_by), row.get("count"))

	return {"labels": list(expenses.keys()), "values": list(expenses.values())}


@frappe.whitelist()
def get_total_incentive(from_date, to_date):
	EmployeeIncentive = frappe.qb.DocType("Employee Incentive")

	result = (
		frappe.qb
		.from_(EmployeeIncentive)
		.select(Sum(EmployeeIncentive.incentive_amount).as_("total"))
		.where(
			(EmployeeIncentive.docstatus == 1) &
			(EmployeeIncentive.payroll_date.between(from_date, to_date))
		)
	).run(as_dict=True)

	return result[0]["total"] or 0


@frappe.whitelist()
def get_dynamic_colors():
	colors = frappe.db.get_value("Page Settings", "Page Settings", "*", as_dict=1)
	return colors


@frappe.whitelist()
def get_monthly_salary_data():
	current_year = getdate().year
	data = {month_name[i]: 0 for i in range(1, 13)}

	salary_slips = frappe.db.get_all(
		"Salary Slip",
		filters={
			"docstatus": 1,
			"start_date": [">=", f"{current_year}-01-01"],
			"end_date": ["<=", f"{current_year}-12-31"]
		},
		fields=["rounded_total", "start_date"]
	)

	if not salary_slips:
		return {}

	for slip in salary_slips:
		month = getdate(slip.start_date).month
		month_label = month_name[month]
		data[month_label] += flt(slip.rounded_total)

	return { "labels": list(data.keys()), "values":  list(data.values())}