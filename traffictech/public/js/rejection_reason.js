// Copyright (c) 2024, Canarys Automations Limited and contributors
// For license information, please see license.txt

const REJECTION_DOCTYPES = [
	"Petty Cash Entry",
];

for (const doctype of REJECTION_DOCTYPES) {
	frappe.ui.form.on(doctype, {
		before_workflow_action: async function (frm) {
			if (frm.selected_workflow_action.includes("Reject") || frm.selected_workflow_action.includes("Request")) {
				frappe.dom.unfreeze();
				frm.workflow_remarks = undefined
				await capture_comments(frm);
				frappe.dom.freeze();
			}
		}
	});

	frappe.ui.form.on(doctype, {
		after_workflow_action: function (frm) {
			if (frm.workflow_remarks) {
				frm.comment_box.on_submit(frm.workflow_remarks);
				setTimeout(() => {
					frm.reload_doc();
				}, 500);
			}
		}
	});
}

function capture_comments(frm) {
	return new Promise((resolve) => {
		let d = new frappe.ui.Dialog({
			title: __("Reason"),
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
				await frappe.db.set_value(frm.doc.doctype, frm.doc.name, "rejection_reason", d.get_value("reason"));
				resolve();
				d.hide();
			},
			secondary_action_label: __("Close"),
			secondary_action: () => d.hide(),
		});

		// flag, used to bind "okay" on enter
		d.confirm_dialog = true;

		// no if closed without primary action
		d.onhide = () => {
			if (!d.primary_action_fulfilled) {
				frappe.dom.unfreeze();
			}
		};

		d.show();
	});
}
