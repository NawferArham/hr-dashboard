// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.listview_settings['Petty Cash Entry'] = {
	onload: function(listview) {
		listview.page.add_inner_button('Download Reports', function() {
			let selected_pm = listview.get_checked_items();

			if (selected_pm.length === 0) {
				frappe.msgprint(__('Please select atleast one Entry.'));
				return;
			}

			let reports = JSON.stringify(selected_pm.map(row => row.name));
			let url = `/api/method/traffictech.traffictech.doctype.petty_cash_entry.petty_cash_entry.download_report_bulkly?pce=${encodeURIComponent(reports)}`;
			window.open(url);

			listview.clear_checked_items()
			listview.refresh();
		});
	},
};
