// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("User", {
	refresh: function(frm) {
		if (!frm.doc.__islocal && frm.doc.enabled && frappe.user.has_role("System Manager")) {
			frm.add_custom_button(__("Impersonate User"), function() {
				frappe.call({
					method: "traffictech.utils.generate_impersonation_url",
					args: {
						"user": frm.doc.name
					},
					callback: function(r) {
						if (!r.exc && r.message) {
							let impersonate_url = `<a href=${r.message}>this link</a>`;
							frappe.msgprint(
								__("Please open {0} in an incognito window to impersonate {1}", [impersonate_url, frm.doc.name]),
							);
						}
					}
				});
			}, __("Password"));
		}
	}
});