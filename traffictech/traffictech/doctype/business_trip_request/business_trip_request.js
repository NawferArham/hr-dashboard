// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on('Business Trip Request', {
	refresh: function(frm) {
		frm.fields_dict.employee_expenses.grid.add_custom_button(__("Add Documents"), function () {
			frm.trigger("upload_ocr_document")
		});
		frm.set_df_property("employee_expenses", "cannot_add_rows", true);
	},

	upload_ocr_document: function(frm) {
		let d = new frappe.ui.Dialog({
			title: __("Attach Document"),
			fields: [
				{
					fieldname: "file_url",
					label: __("File"),
					fieldtype: "Attach",
					reqd: 1,
				},
			],
			primary_action(data) {
				frm.call({
					method: "upload_ocr_document",
					doc: frm.doc,
					args: {
						file_url: data.file_url,
					},
					callback: function (r) {						
						if (r.message === 1) {
							
						}
					},
				});
				d.hide();
			},
			primary_action_label: __("Add"),
		});
		d.show();
	},

	onload: function(frm) {
		if (frm.is_new()) {
			setTimeout(() => {
				frm.call("fetch_user_details");
			}, 100); 
		}
		
	},
});



frappe.ui.form.on('Business Employee Expense', {
	view: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.supplier_invoice_no) {
			return;
		}		
		frm.call({
			method: 'get_invoice_items',
			doc: frm.doc,
			args: {
				invoice: row.supplier_invoice_no
			},
			callback: function (r) {
				if (!r.message) {
					return;
				}
				let d = new frappe.ui.Dialog({
					title: __("Items"),
					size: "large",
					fields: [
						{
							label: "Items",
							fieldname: "items",
							fieldtype: "Table",
							cannot_add_rows: true,
							cannot_delete_rows: true,
							fields: [
							{
								label: "Description",
								fieldname: "description",
								fieldtype: "Data",
								in_list_view: 1,
								read_only: 1,
								columns: 3,
							},
							{
								label: "Qty",
								fieldname: "qty",
								fieldtype: "Float",
								in_list_view: 1,
								columns: 2,
								read_only: 1,
							},
							{
								label: "Rate",
								fieldname: "rate",
								fieldtype: "Currency",
								in_list_view: 1,
								columns: 2,
								read_only: 1,
							},
							{
								label: "Amount",
								fieldname: "amount",
								fieldtype: "Currency",
								in_list_view: 1,
								columns: 2,
								read_only: 1,
							},
							],
							data: r.message,
						},
					],
					primary_action(data) {
						d.hide();
					},
					primary_action_label: __("Close"),
				});
				d.show();
			}
		});
	},
});