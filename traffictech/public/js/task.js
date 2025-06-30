// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Task", {
	refresh(frm) {
		frm.trigger("set_location");
		frm.trigger("add_button_for_time");
		frm.trigger("add_upload_image_btn");
		frm.trigger("add_action_btns");
	},

	set_location: function(frm) {
		if (frm.doc.latitude && frm.doc.longitude) {
			frm.set_df_property('cabinet_location', 'options', `
			<iframe width=100% height="300" 
				id="gmap_canvas" 
				src="https://maps.google.com/maps?q=`+frm.doc.latitude+`,`+frm.doc.longitude+`&t=&z=17&ie=UTF8&iwloc=&output=embed"
				frameborder="0" scrolling="no" marginheight="0" marginwidth="0">
			</iframe>`);
			frm.refresh_field('cabinet_location');
		}
	},

	add_upload_image_btn: function(frm) {
		if (frm.doc.time_log.length > 0) {
			frm.add_custom_button(__('Upload Image'), function () {
				if (!frm.doc.time_log) {
					frappe.throw(__("Please start the Task!"))
				}
				
				// for preventive maintenance
				if (frm.doc.schedule_cabinet) {
					frappe.db.get_value(
						"Preventive Maintenance",
						{ schedule_cabinet: frm.doc.schedule_cabinet, asset_unit: frm.doc.asset_unit, replacement: frm.doc.supervisor ? 1 : 0, docstatus: ["!=", 2]},
						"name",
						(r) => {
							if (r && r.name) {
								frappe.set_route("Form", "Preventive Maintenance", r.name);
							}
						}
					);
				}

				// for inspection improvement
				if (frm.doc.ins_imp_request) {
					frappe.db.get_value(
						"Inspection Improvement",
						{ ins_imp_request: frm.doc.ins_imp_request, asset_unit: frm.doc.asset_unit, replacement: frm.doc.supervisor ? 1 : 0, docstatus: ["!=", 2] },
						"name",
						(r) => {
							if (r && r.name) {
								frappe.set_route("Form", "Inspection Improvement", r.name);
							}
						}
					);
				}

				// for corrective maintenance
				if (frm.doc.cm_request) {
					frappe.db.get_value(
						"Corrective Maintenance",
						{ cm_request: frm.doc.cm_request, asset_unit: frm.doc.asset_unit, replacement: frm.doc.supervisor ? 1 : 0, docstatus: ["!=", 2] },
						"name",
						(r) => {
							if (r && r.name) {
								frappe.set_route("Form", "Corrective Maintenance", r.name);
							}
						}
					);
				}
				
			}).addClass("btn-primary");
		}
	},

	rectification_required: async function(frm) {
		await frappe.db.set_value(frm.doc.doctype, frm.doc.name, "is_group", 1);
		let d = new frappe.ui.Dialog({
			title: __("Rectification"),
			fields: [
				{
					label: 'Assign to Supervisor',
					fieldname: 'supervisor',
					fieldtype: 'Link',
					options: "User",
					ignore_permissions: true,
					reqd: 1,
					get_query: () => {
						return {
							query: "traffictech.tasks.get_supervisors",
						};
					}
				},
				{
					label: 'Description',
					fieldname: 'description',
					fieldtype: 'Small Text',
					reqd: 1
				},
			],
			primary_action_label: __("Create"),
			primary_action: async function(values) {
				frappe.call({
					method: "traffictech.tasks.create_replacement_task",
					args: { doc: frm.doc, description: values.description, supervisor: values.supervisor },
					callback: function (r) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", doc[0].doctype, doc[0].name);
					}
				});
			},
			secondary_action_label: __("Close"),
			secondary_action: () => d.hide(),
		});
		d.show();
	},

	add_button_for_time: function(frm) {
		if (!frm.is_new()) {
			frm.remove_custom_button("Start");
			frm.remove_custom_button("Pause");
			frm.remove_custom_button("Resume");
			frm.remove_custom_button("Complete");

			if (frm.doc.time_log <= 0) {
				frm.add_custom_button(__('Start'), function () {
					frappe.call({
						method: "traffictech.tasks.start_task",
						args: { task_name: frm.doc.name },
						callback: function () {
							frm.reload_doc();
						}
					});
				}).addClass("btn-primary");
			} else if (
				frm.doc.time_log.length > 0 && 
				["Started", "Resumed"].includes(frm.doc.time_log.at(-1).type) &&
				!["Completed", "Cancelled", "In Complete"].includes(frm.doc.status)
			) {
				frm.add_custom_button(__('Pause'), function () {
					frappe.prompt(
						{
							label: 'Reason for Pausing',
							fieldname: 'reason',
							fieldtype: 'Small Text',
							reqd: 1
						},
						function(values) {
							frappe.call({
								method: "traffictech.tasks.pause_task",
								args: { task_name: frm.doc.name, reason: values.reason },
								callback: function() {
									frm.save();
									frm.reload_doc();
								}
							});
						},
						__('Pause Task'),
						__('Submit')
					);
				}).addClass("btn-danger");
			}
			
			if (
				frm.doc.time_log.length > 0 && 
				frm.doc.time_log.at(-1).type === "Paused" && 
				!["Completed", "Cancelled", "In Complete"].includes(frm.doc.status)
			) {
				frm.add_custom_button(__('Resume'), function () {
					frappe.prompt(
						{
							label: 'Reason for Resuming',
							fieldname: 'reason',
							fieldtype: 'Small Text',
							reqd: 1
						},
						function(values) {
							frappe.call({
								method: "traffictech.tasks.resume_task",
								args: { task_name: frm.doc.name, reason: values.reason },
								callback: function() {
									frm.save();
									frm.reload_doc();
								}
							});
						},
						__('Resume Task'),
						__('Submit')
					);
				}).addClass("btn-primary");
			}

			if (
				frm.doc.time_log.length > 0 && 
				["Started", "Resumed"].includes(frm.doc.time_log.at(-1).type) && 
				!["Completed", "Cancelled", "In Complete"].includes(frm.doc.status)
			) {
				frm.add_custom_button(__('Complete'), function () {
					frappe.call({
						method: "traffictech.tasks.complete_task",
						args: { task_name: frm.doc.name },
						callback: function () {
							frm.reload_doc();
						}
					});
				}).addClass("btn-primary");
			}
		}
	},

	add_action_btns: function(frm) {
		if (!frm.is_new() && frm.doc.status != "Cancelled") {
			frm.add_custom_button(__('Cancel Task'), function () {
				frappe.prompt(
					{
						label: 'Reason for Cancelling',
						fieldname: 'reason',
						fieldtype: 'Small Text',
						reqd: 1
					},
					function(values) {
						frm.set_value("status", "Cancelled");
						frm.set_value("cancel_reason", values.reason);
						frm.save();
					},
					__('Cancel Task'),
					__('Cancel')
				);
			}, __("Actions")).addClass("btn-danger");
		}


		if (!frm.is_new() && frm.doc.status != "Completed") {
			frm.add_custom_button(__('Reassign Task'), function () {
				frappe.prompt(
					{
						label: 'New Team',
						fieldname: 'team',
						fieldtype: 'Link',
						options: 'Team',
						reqd: 1
					},
					function(values) {
						if (values.team == frm.doc.team) {
							frappe.throw("Please select different Team!")
						}
						frm.call({
							method: "traffictech.tasks.reassign_task",
							args: { task: frm.doc.name, new_team: values.team},
							callback: function () {
								frm.reload_doc();
							}
						});
					},
					__('Select New Team'),
					__('Assign')
				);
			}, __("Actions"));
		}

		// Change Incident
		if (!frm.is_new() && frm.doc.status != "Completed") {
			frm.add_custom_button(__('Change Incident'), function () {
				let d = new frappe.ui.Dialog({
					title: __("Change Incident"),
					fields: [
						{
							label: 'Incident Type',
							fieldname: 'incident_type',
							fieldtype: 'Link',
							options: "Incident",
							reqd: 1,
							get_query: () => {
								return {
									filters: {
										is_group: 1,
									}
								};
							}
							
						},
						{
							label: 'Incident Category',
							fieldname: 'incident_category',
							fieldtype: 'Link',
							options: "Incident",
							reqd: 1,
							get_query: () => {
								return {
									filters: {
										incident_type: d.get_value("incident_type"),
										is_group: 0,
									}
								};
							}
						},
						{
							label: 'Comments',
							fieldname: 'comments',
							fieldtype: 'Small Text',
						},
					],
					primary_action_label: __("Change"),
					primary_action: async function(values) {
						frappe.call({
							method: "traffictech.tasks.change_incident",
							args: { task: frm.doc.name, incident_type: values.incident_type, incident_category: values.incident_category },
							callback: function (r) {
								frm.comment_box.on_submit(`Incident Category Changed to ${values.incident_category}, Comments: ${values.comments}`);
							}
						});
						d.hide();
					},
					secondary_action_label: __("Close"),
					secondary_action: () => d.hide(),
				});
				d.show();
			}, __("Actions"));
		}
	}
});