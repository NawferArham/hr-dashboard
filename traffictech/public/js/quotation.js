// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quotation", {
	refresh(frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Download PDF"), function(){
				open_url_post("/api/method/frappe.utils.print_format.download_pdf", {
					doctype: frm.doc.doctype,
					name: frm.doc.name
				}, 1);
			
			});
		}
	},

	print_with_tax: function(frm) {
		if(frm.doc.print_with_tax) {
			frm.set_value("print_with_remarks", 0);
			frm.set_value("print_only_qty", 0);
		}
	},

	print_with_remarks: function(frm) {
		if(frm.doc.print_with_remarks) {
			frm.set_value("print_with_tax", 0);
			frm.set_value("print_only_qty", 0);
		}
	},

	print_only_qty: function(frm) {
		if(frm.doc.print_only_qty) {
			frm.set_value("print_with_tax", 0);
			frm.set_value("print_with_remarks", 0);
		}
	}
});