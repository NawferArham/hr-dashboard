// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Estimation", {
	refresh(frm) {
		frm.set_df_property("items", "cannot_delete_rows", true);
		frm.set_df_property("items", "cannot_add_rows", true);

		if (frm.doc.docstatus == 1) {
			frm.add_custom_button('Quotation', function() {
				frm.call({
					method:"create_quotation",
					doc: frm.doc,
					callback: function (r) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", doc[0].doctype, doc[0].name);
					}
				})
			}, 'Create');
		}

		frm.set_query('party_type', function() {
			return {
				filters: {
					name: ['in', ['Customer', 'Lead', 'Prospect']]
				}
			};
		});
	},
});


frappe.ui.form.on("Estimation Item Group", {
	add_items(frm, cdt, cdn) {
		let row = locals[cdt][cdn]
		open_item_dialog(frm, row.description)
	},
});


function open_item_dialog(frm, group, table) {
	const existing_items = frm.doc.items.filter(item => item.group === group);
  
	let dialog = new frappe.ui.Dialog({
	  title: `Add Items for Group: ${group}`,
	  size: "extra-large",
	  static: true,
	  fields: [
		{
		  label: 'Items',
		  fieldname: 'items',
		  fieldtype: 'Table',
		  fields: [
			{
				fieldtype: 'Link',
				fieldname: 'item_code',
				label: 'Product Code',
				options: 'Item',
				in_list_view: 1,
				reqd: 1,
				columns: 1,
				read_only: frm.doc.docstatus == 1 ? 1 : 0,
				get_query: () => ({ filters: { disabled: 0 } }),
			},
			{ fieldtype: 'Data', fieldname: 'item_name', label: 'Product Name', in_list_view: 1, columns: 1, read_only: 1 },
			{ fieldtype: 'Link', fieldname: 'uom', label: 'UOM', options: 'UOM', in_list_view: 1, columns: 0.5 },
			{ fieldtype: 'Float', fieldname: 'qty', label: 'Qty', in_list_view: 1, columns: 0.5 },
			{ fieldtype: 'Column Break', fieldname: 'clm_break' },
			{ fieldtype: 'Currency', fieldname: 'list_price', label: 'List Price', in_list_view: 1, columns: 1, options: "currency"},
			{ fieldtype: 'Percent', fieldname: 'logistic_percent', label: 'Logistic %', in_list_view: 1, columns: 0.5 },
			{ fieldtype: 'Currency', fieldname: 'logistic_amount', label: 'Logistic Amount', read_only: 1, options: "currency" },
			{ fieldtype: 'Currency', fieldname: 'total_cost', label: 'Total Cost', in_list_view: 1, read_only: 1, columns: 1, options: "currency" },
			{ fieldtype: 'Currency', fieldname: 'installation_cost', label: 'Installation', in_list_view: 1, columns: 0.5, options: "currency" },
			{ fieldtype: 'Section Break', fieldname: 'sec_break' },
			{ fieldtype: 'Percent', fieldname: 'profit_percent', label: 'Profit %', in_list_view: 1, columns: 0.5 },
			{ fieldtype: 'Currency', fieldname: 'profit_amount', label: 'Profit Amount', read_only: 1, options: "currency"},
			{ fieldtype: 'Column Break', fieldname: 'clm_break2' },
			{ fieldtype: 'Currency', fieldname: 'unit_price', label: 'Unit Price', read_only: 1, in_list_view: 1, columns: 0.5, options: "currency" },
			{ fieldtype: 'Currency', fieldname: 'total', label: 'Total', in_list_view: 1, read_only: 1, columns: 1, options: "currency" },
			{ fieldtype: 'Small Text', fieldname: 'internal_remarks', label: 'Internal Remarks', in_list_view: 1, columns: 1 },
			{ fieldtype: 'Small Text', fieldname: 'external_remarks', label: 'External Remarks', in_list_view: 1, columns: 1 },
			{ fieldtype: 'Data', fieldname: 'row_name', label: 'Row Name', read_only: 1, hidden: 1},
		  ],
		  data: existing_items.map(item => ({
			item_code: item.item_code,
			item_name: item.item_name,
			uom: item.unit,
			qty: item.qty,
			list_price: item.list_price,
			logistic_percent: item.logistic_percent,
			logistic_amount: item.logistic_amount,
			total_cost: item.total_cost,
			installation_cost: item.installation_cost,
			profit_percent: item.profit_percent,
			profit_amount: item.profit_amount,
			unit_price: item.unit_price,
			total: item.total,
			internal_remarks: item.internal_remarks,
			external_remarks: item.external_remarks,
			row_name: item.name,
		  })),
		  get_data: () => dialog.fields_dict.items.df.data,
		}
	  ],
	  primary_action_label: 'Save Items',
	  primary_action(values) {
		frm.call({
			method:"add_items",
			doc: frm.doc,
			args: {"items": values.items, "group": group},
			callback: function (r) {
				frm.refresh_field('items');
				frm.dirty();
				dialog.hide();
			}
		})
	  },
	  secondary_action_label: 'Close',
	  secondary_action() {
		dialog.hide();
	  },
	});
	const grid = dialog.fields_dict.items.grid;

	grid.fields_map.qty.onchange = function() {
		update_amount(dialog);
	};
	grid.fields_map.list_price.onchange = function() {
		update_amount(dialog);
	};
	grid.fields_map.logistic_percent.onchange = function() {
		update_amount(dialog);
	};
	grid.fields_map.profit_percent.onchange = function() {
		update_amount(dialog);
	};
	grid.fields_map.installation_cost.onchange = function() {
		update_amount(dialog);
	};
	grid.fields_map.item_code.onchange = function() {
		fetch_item_details(dialog);
	};
  
	dialog.show();

	// Scrollable Table
	setTimeout(() => {
		const grid = dialog.fields_dict.items.grid;
	  
		if (grid) {
		  const $wrapper = $(grid.wrapper).closest('.frappe-control');
	  
		  $wrapper.css({
			'overflow-x': 'auto',
			'display': 'block',
			'width': '100%'
		  });
	  
		  $(grid.wrapper).css({
			'min-width': '1600px',
			'display': 'inline-block'
		  });
		}
	}, 300);
}
  
function update_amount(dialog) {
	let items = dialog.get_value("items");
	items.forEach((row, idx) => {
		if (row && row.profit_percent && row.profit_percent > 100) {
			row.profit_percent = 0;
			frappe.throw(__("Percentage need to be less than 100!"));
			return
		}
		if (row && row.qty && row.list_price) {
			row.total_cost = flt(row.qty) * flt(row.list_price)

			if (row.logistic_percent) {
				row.logistic_amount = (row.total_cost * flt(row.logistic_percent)) / 100
				row.total_cost = flt(row.total_cost) + flt(row.logistic_amount)
			}
			
			if (row.profit_percent) {
				let total_cost_with_installation = flt(row.total_cost) + flt(row.installation_cost)
				row.profit_amount = (total_cost_with_installation * flt(row.profit_percent)) / 100
			}

			row.total = flt(row.total_cost) + flt(row.profit_amount) + flt(row.installation_cost)
			row.unit_price = flt(row.total) / flt(row.qty)
		}
	});
	dialog.refresh()
}

function fetch_item_details(dialog) {
	let items = dialog.get_value("items");
	items.forEach((row, idx) => {
		if (!row.item_name) {
			frappe.db.get_value('Item', row.item_code, ['item_name', 'stock_uom'])
			.then(r => {
				if (r.message) {
					row.item_name = r.message.item_name;
					row.uom = r.message.stock_uom;
					dialog.refresh()
				}
			});
		}
	});
}