# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import datetime
import frappe
from frappe.query_builder import DocType

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Employee Code", "fieldname": "employee_code", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": "Document", "fieldname": "document", "fieldtype": "Data", "width": 150},
        {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

    document_filter = filters.get("document")
    status_filter = filters.get("status")
    month = filters.get("month")
    year = filters.get("year")
    today = datetime.date.today()

    # Build date range filter if month and year are given
    date_start, date_end = None, None
    if month and year:
        month_number = datetime.datetime.strptime(month, "%B").month
        date_start = datetime.date(int(year), month_number, 1)
        next_month = month_number % 12 + 1
        next_year = int(year) + (1 if next_month == 1 else 0)
        date_end = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)

    doc_map = {
        "Passport": "valid_upto",
        "Health Card": "expiry",
        "KSA Visa": "custom_expiry_ksa_visa",
        "UAE Visa": "custom_expiry_uae_visa",
        "QID": "qid_expiry"
    }

    doc_types = [document_filter] if document_filter else doc_map.keys()
    data = []

    for doc_type in doc_types:
        fieldname = doc_map[doc_type]

        filters = {
            "status": "Active"
        }

        if date_start and date_end:
            filters[f"{fieldname}"] = ["between", [date_start, date_end]]
        else:
            filters[f"{fieldname}"] = ["!=", None]

        employees = frappe.get_all("Employee", filters=filters, fields=["name", "employee_name", fieldname])

        for emp in employees:
            expiry_date = emp.get(fieldname)
            if not expiry_date:
                continue

            status = "Expired" if expiry_date < today else "Valid"
            if status_filter and status != status_filter:
                continue

            data.append({
                "employee_code": emp.name,
                "employee_name": emp.employee_name,
                "document": doc_type,
                "expiry_date": expiry_date,
                "status": status
            })

    return columns, sorted(data, key=lambda x: x["expiry_date"])
