// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	refresh(frm) {
		frm.fields_dict.ctc.$wrapper.on('click', function() {
			if (frm.doc.name && frm.doc.ctc) {
				frappe.call({
					method: "traffictech.utils.get_ssa_of_emp",
					args: { employee: frm.doc.name},
					callback: function (r) {
						if (r.message) {
							frappe.set_route("Form", "Salary Structure Assignment", r.message);
						}
					}
				});
			}
		});
	},
});