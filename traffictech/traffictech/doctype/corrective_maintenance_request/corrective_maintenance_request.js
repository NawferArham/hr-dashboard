// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Corrective Maintenance Request", {
	refresh(frm) {
		frm.set_query('incident_type', function() {
			return {
				filters: {
					is_group: 1
				}
			};
		});

		frm.set_query('incident_category', function() {
			return {
				filters: {
					incident_type: frm.doc.incident_type,
					is_group: 0,
				}
			};
		});


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
	},


	before_cancel: function(frm) {
		return new Promise((resolve, reject) => {
			let d = new frappe.ui.Dialog({
				title: __("Cancel Reason"),
				static: 1,
				fields: [
					{
						label: 'Reason',
						fieldname: 'reason',
						fieldtype: 'Small Text',
						reqd: 1
					},
				],
				primary_action_label: __("Submit"),
				primary_action: async function() {
					frm.workflow_remarks = d.get_value("reason");
					await frappe.db.set_value(frm.doc.doctype, frm.doc.name, "cancel_reason", d.get_value("reason"));
					resolve();
					d.hide();
				},
			});
		});
	}
});
