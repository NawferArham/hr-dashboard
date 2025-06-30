// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.listview_settings['Inspection Improvement Request'] = {
	onload: function(listview) {
		listview.page.add_inner_button('Change Team', function() {
			let selected_schedules = listview.get_checked_items();

			if (selected_schedules.length === 0) {
				frappe.msgprint(__('Please select Schedule first.'));
				return;
			}

			let d = new frappe.ui.Dialog({
				title: 'Assign to Another Team',
				fields: [
					{
						label: 'New Team',
						fieldname: 'team',
						fieldtype: 'Link',
						options: 'Team',
						reqd: 1
					},
				],
				primary_action_label: 'Assign',
				primary_action(values) {
					let schedules = selected_schedules.map(row => row.name);

					frappe.call({
						method: 'traffictech.traffictech.doctype.schedule_cabinet.schedule_cabinet.change_team_bulkly',
						args: {
							schedules: schedules,
							team: values.team,
							from_task: 0,
							type_: "INS",
						},
						callback: function(response) {
							listview.clear_checked_items()
							frappe.dom.unfreeze(); 
							frappe.msgprint(__(`Assignment in Progress will update shortly...`));
							listview.refresh();
							d.hide();
						},
						error: function () {
							frappe.dom.unfreeze();
						}
					});
				}
			});
			d.show();
		});
	}
};
