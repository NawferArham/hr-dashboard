# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint
from pypika import Order
from frappe.query_builder.functions import Sum


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_data(filters):
	data = []

	ee = frappe.qb.DocType("Expense Entry")


	if filters.get("show_summary"):
		query = (
			frappe.qb.from_(ee)
			.select(
				ee.name,
				ee.supplier,
				Sum(ee.base_total).as_("base_total"),
				Sum(ee.base_discount_amount).as_("base_discount_amount"),
				Sum(ee.base_tax_and_charges).as_("base_tax_and_charges"),
				Sum(ee.base_grand_total).as_("base_grand_total")
			)
			.orderby(ee.supplier_invoice_date, ee.name, order=Order.desc)
			.where(ee.docstatus == 1)
			.groupby(ee.supplier)
		)
	else:
		query = (
			frappe.qb.from_(ee)
			.select(
				ee.name,
				ee.employee,
				ee.employee_name,
				ee.currency,
				ee.conversion_rate,
				ee.supplier,
				ee.supplier_invoice_no,
				ee.supplier_invoice_date,
				ee.category,
				ee.base_total,
				ee.base_discount_amount,
				ee.base_tax_and_charges,
				ee.base_grand_total,
			)
			.orderby(ee.supplier_invoice_date, ee.name, order=Order.desc)
			.where(ee.docstatus == 1)
		)

	if filters.get("from_date"):
		query = query.where(ee.supplier_invoice_date >= filters.from_date)

	if filters.get("to_date"):
		query = query.where(ee.supplier_invoice_date <= filters.to_date)

	if filters.get("supplier"):
		query = query.where(ee.supplier == filters.supplier)
	
	if filters.get("employee"):
		query = query.where(ee.employee == filters.employee)

	data = query.run(as_dict=1)
	
	return data


def get_columns(filters):
	hidden = 0
	if filters.get("show_summary"):
		hidden = 1
	columns = [
		{"label": _("Invoice Date"), "fieldname": "supplier_invoice_date", "fieldtype": "Date", "width": 80, "hidden": hidden},
		{"label": _("supplier"), "fieldname": "supplier", "fieldtype": "Data", "width": 160},
		{"label": _("Invoice No"), "fieldname": "supplier_invoice_no", "fieldtype": "Data", "width": 120, "hidden": hidden},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 120, "hidden": hidden},
		{"label": _("Employee"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160, "hidden": hidden},
		{"label": _("Total"), "fieldname": "base_total", "fieldtype": "Float", "width": 150},
		{"label": _("Discount Amount"), "fieldname": "base_discount_amount", "fieldtype": "Float", "width": 160},
		{"label": _("Tax & Charges"), "fieldname": "base_tax_and_charges", "fieldtype": "Float", "width": 160},
		{"label": _("Grand Total"), "fieldname": "base_grand_total", "fieldtype": "Float", "width": 160},
	]
	return columns

