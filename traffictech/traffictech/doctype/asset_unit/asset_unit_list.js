// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.listview_settings['Asset Unit'] = {
	onload: function(listview) {
		listview.page.add_inner_button('Bulk Schedule', function() {
			let selected_tasks = listview.get_checked_items();

			if (selected_tasks.length === 0) {
				frappe.msgprint(__('Please select Assets first.'));
				return;
			}

			let d = new frappe.ui.Dialog({
				title: 'Schedule Asset Unit',
				fields: [
					{
						label: 'Team',
						fieldname: 'team',
						fieldtype: 'Link',
						options: 'Team',
						reqd: 1,
					},
					{
						label: 'Fiscal Year',
						fieldname: 'fiscal_year',
						fieldtype: 'Link',
						options: 'Fiscal Year',
						reqd: 1,
						default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today())
					},
					{
						fieldname: 'col_break',
						fieldtype: 'Column Break',
					},
					{
						label: 'Assign Date',
						fieldname: 'schedule_date',
						fieldtype: 'Date',
						reqd: 1
					},
					{
						label: 'Schedule Month',
						fieldname: 'schedule_month',
						fieldtype: 'Select',
						options: "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
						reqd: 1
					},
					{
						fieldname: 'sec_break',
						fieldtype: 'Section Break',
					},
					{
						label: 'Selected Units',
						fieldname: 'units',
						fieldtype: 'Table',
						cannot_add_rows: false,
						in_place_edit: true,
						reqd: 1,
						fields: [
							{
								fieldname: 'asset_unit',
								fieldtype: 'Link',
								options: 'Asset Unit',
								label: 'Asset Unit',
								reqd: 1,
								in_list_view: 1
							},
							{
								fieldname: 'asset_name',
								fieldtype: 'Data',
								label: 'Asset Name',
								fetch_from: 'asset_unit.asset_name',
								read_only: 1,
								in_list_view: 1
							}
						]
					},
					
				],
				primary_action_label: 'Schedule',
				primary_action(values) {
					let units = values.units.map(row => row.asset_unit);

					if (units.length === 0) {
						frappe.msgprint(__('Please select at least one Asset.'));
						return;
					}

					frappe.dom.freeze(__("Scheduling Asset Unit..."));

					frappe.call({
						method: 'traffictech.traffictech.doctype.asset_unit.asset_unit.bulk_schedule_asset_unit',
						args: {
							asset_units: units,
							team: values.team,
							schedule_date: values.schedule_date,
							schedule_month: values.schedule_month,
							fiscal_year: values.fiscal_year,
						},
						callback: function(response) {
							listview.clear_checked_items()
							frappe.dom.unfreeze(); 
							frappe.msgprint(__('Bulk Schedule successfull!'));
							listview.refresh();
							d.hide();
						},
						error: function () {
							frappe.dom.unfreeze();
						}
					});
				}
			});

			let units = d.fields_dict.units.df.data = [];
			selected_tasks.forEach(unit => {
				units.push(
					{ 
						asset_unit: unit.name,
						asset_name: unit.asset_name,
					}
				);
			});
			d.fields_dict.units.grid.refresh();

			d.show();
		});
	}
};
