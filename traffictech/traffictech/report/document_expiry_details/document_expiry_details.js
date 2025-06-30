// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.query_reports["Document Expiry Details"] = {
    filters: [
        {
            fieldname: "month",
            label: "Expiry Month",
            fieldtype: "Select",
            options: [
                "", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ],
            default: ""
        },
        {
            fieldname: "year",
            label: "Expiry Year",
            fieldtype: "Int",
            default: (new Date()).getFullYear()
        },
        {
            fieldname: "document",
            label: "Document",
            fieldtype: "Select",
            options: [
                "", "QID","Passport", "Health Card", "KSA Visa", "UAE Visa"
            ],
            default: ""
        },
        {
            fieldname: "status",
            label: "Status",
            fieldtype: "Select",
            options: ["", "Expired", "Valid"],
            default: ""
        }
    ]
};
