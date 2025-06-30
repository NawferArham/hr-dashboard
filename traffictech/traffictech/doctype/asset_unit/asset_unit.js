// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Asset Unit", {
	refresh(frm) {
		if (frm.doc.latitude && frm.doc.longitude) {
			frm.set_df_property('location', 'options', `
			<iframe width=100% height="300" 
				id="gmap_canvas" 
				src="https://maps.google.com/maps?q=`+frm.doc.latitude+`,`+frm.doc.longitude+`&t=&z=17&ie=UTF8&iwloc=&output=embed"
				frameborder="0" scrolling="no" marginheight="0" marginwidth="0">
			</iframe>`);
			frm.refresh_field('location');
		}


		if (!frm.is_new()){
			frm.add_custom_button('Request for Inspection', function() {
				frm.call({
					method:"create_inspection_request",
					doc: frm.doc,
					callback: function (r) {
						var doc = frappe.model.sync(r.message)				
						frappe.set_route("Form", doc[0].doctype, doc[0].name);
					}
				})
			}, "Create");

			frm.add_custom_button('Sync Task', function() {
				frm.call({
					method:"sync_tasks",
					doc: frm.doc,
					callback: function (r) {
						if (r.message) {
							frappe.show_alert({
								message: __("Tasks are Updated"),
								indicator: "green",
							}, 5);
						}
					}
				})
			});
		}
	},
});
