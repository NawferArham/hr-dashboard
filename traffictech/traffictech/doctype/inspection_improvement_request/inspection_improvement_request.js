// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Inspection Improvement Request", {
	refresh(frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Change Team'), function () {
				frappe.prompt(
					{
						label: 'New Team',
						fieldname: 'team',
						fieldtype: 'Link',
						options: 'Team',
						reqd: 1
					},
					function(values) {
						frm.call({
							method: "change_team",
							doc: frm.doc,
							args: { team: values.team},
							callback: function () {
								frm.reload_doc();
							}
						});
					},
					__('Select New Team'),
					__('Assign')
				);
			}).addClass("btn-primary");
		} 
	},
	team: function(frm) {
		frm.call("add_team_members");
	}
});
