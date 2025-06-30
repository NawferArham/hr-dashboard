// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incident", {
	refresh(frm) {
		frm.set_query('incident_type', function() {
			return {
				filters: {
					is_group: 1,
				}
			};
		});
	},

	is_group: function(frm) {
		frm.set_query('incident_type', function() {
			return {
				filters: {
					is_group: 1,
				}
			};
		});
	}
});
