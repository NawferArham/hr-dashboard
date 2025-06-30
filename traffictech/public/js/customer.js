// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer", {
	refresh(frm) {
		frm.trigger("show_activities");
	},
	show_activities(frm) {
		if (frm.doc.docstatus == 1) return;

		const crm_activities = new erpnext.utils.CRMActivities({
			frm: frm,
			open_activities_wrapper: $(frm.fields_dict.open_activities_html.wrapper),
			all_activities_wrapper: $(frm.fields_dict.all_activities_html.wrapper),
			form_wrapper: $(frm.wrapper),
		});
		crm_activities.refresh();
	}
});