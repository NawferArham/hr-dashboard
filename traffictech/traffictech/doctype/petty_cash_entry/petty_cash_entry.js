// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.provide("traffictech");
frappe.ui.form.on('Petty Cash Entry', {
	onload: function (frm) {
		frm.set_df_property("bills", "cannot_add_rows", true);
		if (frm.is_new()) {
			frm.doc.bills = [];
			frm.refresh_fields("bills")
		}
	},
	setup: function (frm) {
		if (frm.is_new()) {
			frm.clear_table('bills');
		}
	},
	form_render: function (frm) {
		// For all attach buttons on form
		$(document).on('shown.bs.modal', '.modal', function () {
			const $dialog = $(this);
			if ($dialog.find('.attach-public-switch').length) {
				$dialog.find('.attach-public-switch').closest('.form-group').hide(); // hides the public/private switch
			}
		});
	},
	refresh: function (frm) {
		const msg = sessionStorage.getItem('scanner_message');
		if (msg) {
			frappe.msgprint(__(`These Supplier Invoices are already added in Some Entries:<br><b>${msg.join(', ')}</b>`));
			sessionStorage.removeItem('scanner_message');
		}

		frm.fields_dict.bills.grid.add_custom_button(__("Attach"), function () {
			frm.trigger("upload_ocr_document")
		});
		frm.fields_dict.bills.grid.add_custom_button(__("Scan"), function () {
			frm.trigger("scan_document")
		});
		frm.fields_dict["bills"].$wrapper.find('.grid-body .rows').find(".grid-row").each(function (i, item) {
			let d = locals[frm.fields_dict["bills"].grid.doctype][$(item).attr('data-name')];
			if (d["s_qty"] == d["c_qty"]) {
				$(item).find('[data-fieldname="view_items"]').empty().append("<button class='btn btn-xs btn-success' id='view_items'>View Items</button>").click(function () {
					let cdn = $(item).attr('data-name')
					let cdt = 'Petty Cash Entry Bill'
					frm.script_manager.trigger('view_items', cdt, cdn)
				})
			}
		});

		if (!frm.is_new()) {
			frm.add_custom_button(__('Download Report'), function () {
				let url = `/api/method/traffictech.traffictech.doctype.petty_cash_entry.petty_cash_entry.download_report?pce=${frm.doc.name}`;
				window.open(url);
			});
		}

		if (frm.timeline && frm.timeline.wrapper) {
			frm.timeline.wrapper.hide();
		}
	},
	upload_ocr_document: function (frm) {
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
				if (!data.file_url) {
					frappe.msgprint(__("Please upload a file first."));
					return;
				}

				frappe.dom.freeze(__("Processing document, please wait..."));

				frm.call({
					method: "ocr_document_file",
					doc: frm.doc,
					args: {
						file_url: data.file_url,
					}, callback: function (r) {
						if (r.message) {
							for (let output of r.message) {
								let row = frm.add_child("bills", {
									"attachment": data.file_url,
									'json_data': JSON.stringify(output),
									'document_type': output.document_type,
									'supplier': output.supplier,
									'supplier_invoice_no': output.supplier_invoice_no,
									'supplier_invoice_date': output.date,
									'currency': output.currency,
									'category': output.category,
									'total_qty': output.total_quantity,
									'total': output.subtotal,
									'tax_and_charges': output.tax,
									'discount_amount': output.discount,
									'grand_total': output.grand_total
								});

								frm.set_value("currency", output.currency)

								var items = output.items || [];
								for (let t of items) {
									let row = frm.add_child("items", {
										description: t.description,
										qty: t.qty,
										rate: t.rate,
										amount: t.amount,
										// bill_reference: row_name,
										supplier_invoice_no: output.supplier_invoice_no
									});
								}
								frm.refresh_field("bills");
								frm.refresh_field("items");
								frappe.dom.unfreeze();
							}
						} else {
							frappe.msgprint(__("Failed to extract data. Please upload a clearer image or PDF."));
						}
					},
					error: function () {
						frappe.dom.unfreeze();
						frappe.msgprint(__("An error occurred while processing the document."));
					}
				});
				d.hide();
			},
			primary_action_label: __("Add"),
		});
		d.show();
	},

	scan_document: function (frm) {
		frappe.require(['scanner.bundle.css', 'scanner.bundle.js']).then(() => {
			let d = new frappe.ui.Dialog({
				title: __("Scan and Upload"),
				size: window.innerWidth < 768 ? "full" : "extra-large", // Full-screen on mobile
				no_scroll: false,
				fields: [
					{
						fieldname: "html_wrapper",
						fieldtype: "HTML",
					},
				],
				primary_action_label: __("Close"),
				primary_action: function () {
					d.hide();
				}
			});

			d.show();
			d.$wrapper.find('.modal-content').css({
				'width': '100%',
				'height': '800px',
				'margin': '0 auto',
				'left': '50%',
				'transform': 'translateX(-50%)'
			});

			let container = d.fields_dict.html_wrapper.$wrapper;
			container.html('<div id="scanner-container" style="width:100%; height:400px;"></div>');

			setTimeout(function () {
				new traffictech.DocScanner({
					wrapper: $("#scanner-container"),
					page: d,
					form: frm.doc.name,
					liveDetection: frappe.boot.live_detection,
					onImagesUploaded: async function (images) {
						if (!images.files) {
							return;
						}

						frappe.dom.freeze(__("Processing document, please wait..."));

						await frm.call({
							method: "scan_documents",
							doc: frm.doc,
							args: {
								files: images.files,
							}, callback: async function (r) {
								if (r.message.outputs && r.message.outputs.length > 0) {
									await Promise.all(r.message.outputs.map(async (output) => {
										let row = frm.add_child("bills", {
											"attachment": output.file_url,
											'json_data': JSON.stringify(output),
											'document_type': output.document_type,
											'supplier': output.supplier,
											'supplier_invoice_no': output.supplier_invoice_no,
											'supplier_invoice_date': output.date,
											'currency': output.currency,
											'category': output.category,
											'total_qty': output.total_quantity,
											'total': output.subtotal,
											'tax_and_charges': output.tax,
											'discount_amount': output.discount,
											'grand_total': output.grand_total
										});

										var items = output.items || [];
										items.forEach(t => {
											frm.add_child("items", {
												description: t.description,
												qty: t.qty,
												rate: t.rate,
												amount: t.amount,
												supplier_invoice_no: output.supplier_invoice_no
											});
										});
									}));

									await frm.refresh_field("bills");
									await frm.refresh_field("items");
									await frm.save();

									// Store it to show after reload
									sessionStorage.setItem('scanner_message', r.message.message);

									frm.refresh();
									frappe.dom.unfreeze();
									window.location.reload();
								} else {
									frappe.dom.unfreeze();
									if (r.message.message) {
										const msg = `These Supplier Invoices are already added in Some Entries:<br><b>${r.message.message.join(', ')}</b>`;
										frappe.msgprint(__(msg));
									} else {
										frappe.msgprint(__("Failed to extract data. Please upload a clearer image or PDF."));
									}
								}
							},
							error: function () {
								frappe.dom.unfreeze();
								frappe.msgprint(__("An error occurred while processing the document."));
							}
						});
						d.hide();
					}
				});
			}, 500);
		});
	},

	show_activity: function(frm) {
		if (frm.timeline && frm.timeline.wrapper) {
			frm.timeline.wrapper.show();
		}
	},

	before_workflow_action: async function (frm) {
		if (frm.selected_workflow_action.includes("Revise")) {
			frappe.dom.unfreeze();
			await frm.call({
				method: 'email_to_initiator',
				doc: frm.doc,
				callback: function (r) {
					frappe.dom.freeze();
				}
			});
		}

		if (frm.selected_workflow_action.includes("Comment")) {
			frappe.dom.unfreeze();
			frm.workflow_comments = undefined
			await capture_comments(frm);
			frappe.dom.freeze();
		}
	},

	after_workflow_action: function (frm) {
		if (frm.workflow_comments) {
			frm.comment_box.on_submit(frm.workflow_comments);
			setTimeout(() => {
				frm.reload_doc();
			}, 500);
		}
	}
});

function capture_comments(frm) {
	return new Promise((resolve) => {
		let d = new frappe.ui.Dialog({
			title: __("Comment"),
			fields: [
				{
					label: 'Comment',
					fieldname: 'comment',
					fieldtype: 'Small Text',
					reqd: 1
				},
			],
			primary_action_label: __("ADD"),
			primary_action: async function() {
				frm.workflow_comments = d.get_value("comment");
				resolve();
				d.hide();
			},
			secondary_action_label: __("Close"),
			secondary_action: () => d.hide(),
		});

		d.confirm_dialog = true;

		d.onhide = () => {
			if (!d.primary_action_fulfilled) {
				frappe.dom.unfreeze();
			}
		};

		d.show();
	});
}


frappe.ui.form.on('Petty Cash Entry Bill', {
	status: function (frm, cdt, cdn) {
		if (frm.doc.workflow_state == "Draft") {
			frappe.model.set_value(cdt, cdn, "status", "Pending")
			frappe.throw(__("You are not allowed to change the Approval Status"))
		}
	},
	view_items: function (frm, cdt, cdn) {
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
				let active_dialog = false;
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
							read_only: 1,
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
								{
									label: "Status",
									fieldname: "status",
									fieldtype: "Select",
									options: ["", "Approve", "Reject"],
									in_list_view: 1,
									columns: 1,
								},
							],
						},
					],
					primary_action_label: 'Update Status',
					primary_action(values) {
						frm.call({
							method:"update_item_status",
							doc: frm.doc,
							args: {"items": values.items, "invoice": row.supplier_invoice_no},
							callback: function (r) {
								frm.refresh_field('items');
								frm.dirty();
								d.hide();
							}
						})
					},
					secondary_action_label: 'Close',
					secondary_action() {
						d.hide();
					},
				});
				
				active_dialog = true;
				d.show();
				if (active_dialog) {
					d.hide();
				}

				let items_table = d.fields_dict.items.df;
				items_table.data = [];
				r.message.forEach(item => {
					items_table.data.push({
						description: item.description,
						qty: item.qty,
						rate: item.rate,
						amount: item.amount,
						status: item.status
					});
				});

				d.fields_dict.items.grid.refresh();
			}
		});
	},

});


function get_ocr_document_file(frm, row_name, file, cdt, cdn) {
	if (!file) {
		frappe.msgprint(__("Please upload a file first."));
		return;
	}

	frm.call({
		method: 'ocr_document_file',
		doc: frm.doc,
		args: {
			file_url: file
		},
		callback: function (r) {
			if (r.message) {
				frappe.model.set_value(cdt, cdn, {
					'json_data': JSON.stringify(r.message),
					'document_type': r.message.document_type,
					'supplier': r.message.supplier,
					'supplier_invoice_no': r.message.supplier_invoice_no,
					'supplier_invoice_date': r.message.date,
					'currency': r.message.currency,
					'category': r.message.category,
					'tax_and_charges': r.message.tax,
					'discount_amount': r.message.discount
				})

				var items = r.message.items || [];
				for (let t of items) {
					let row = frm.add_child("items", {
						description: t.description,
						qty: t.qty,
						rate: t.rate,
						amount: t.amount,
						// bill_reference: row_name,
						supplier_invoice_no: r.message.supplier_invoice_no
					});
				}
				frm.refresh_field("items");
				// calculate_total(frm);
			} else {
				frappe.msgprint(__("Failed to extract data. Please upload a clearer image or PDF."));
			}
		}
	});
}
