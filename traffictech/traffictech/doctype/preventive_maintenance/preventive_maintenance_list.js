// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.listview_settings['Preventive Maintenance'] = {
	onload: function(listview) {
		listview.page.add_inner_button('Download Report', function() {
			let selected_reports = listview.get_checked_items();

			if (selected_reports.length === 0) {
				frappe.msgprint(__('Please select atleast one report.'));
				return;
			}

			let reports = JSON.stringify(selected_reports.map(row => row.name));
			let url = `/api/method/traffictech.traffictech.doctype.preventive_maintenance.preventive_maintenance.download_reports?reports=${encodeURIComponent(reports)}`;
			window.open(url);

			listview.clear_checked_items()
			listview.refresh();
		});

		listview.page.add_inner_button('Download Comments', function() {
			let selected_pm = listview.get_checked_items();

			if (selected_pm.length === 0) {
				frappe.msgprint(__('Please select atleast one Maintenance.'));
				return;
			}

			let reports = selected_pm.map(row => row.name);

			frappe.call({
				method: "traffictech.traffictech.doctype.preventive_maintenance.preventive_maintenance.download_comments",
				args: {
					pm: reports
				},
				callback: function (r) {
					if (!r.exc) {
						frappe.msgprint(__('Export started. You will be notified when it’s ready.'));
					}
				}
			});


			listview.clear_checked_items()
			listview.refresh();
		});

		frappe.realtime.on("comments_export_complete", function(data) {
			frappe.msgprint({
				title: __('Export Ready'),
				indicator: 'green',
				message: __('Your export is ready. <a href="{0}" target="_blank">Click here to download</a>.', [data.download_url])
			});
		});

	},
	add_fields: ["status"],
	has_indicator_for_draft: 1,
	get_indicator: function (doc) {
		if (doc.status === 'Pending') {
			return ['Pending', 'orange', 'status,=,' + doc.status];
		} else if (doc.status === 'Working') {
			return ['Working', 'blue', 'status,=,' + doc.status];
		} else if (doc.status === 'Completed') {
			return ['Completed', 'green', 'status,=,' + doc.status];
		} else if (doc.status === 'In Review') {
			return ['In Review', 'cyan', 'status,=,' + doc.status];
		} else if (doc.status === 'Approved') {
			return ['Approved', 'green', 'status,=,' + doc.status];
		} else if (doc.status === 'Cancelled') {
			return ['Cancelled', 'gray', 'status,=,' + doc.status];
		}
	}
};
