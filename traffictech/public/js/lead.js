// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead", {
	refresh(frm) {
		setTimeout(() => {
			frm.remove_custom_button("Opportunity", "Create");
		}, 500);

		frm.add_custom_button('Opportunity ', function() {
			frappe.model.open_mapped_doc({
				method: "erpnext.crm.doctype.lead.lead.make_opportunity",
				frm: frm,
			});
		}, "Create");
	},
});