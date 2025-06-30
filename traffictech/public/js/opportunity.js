// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Opportunity", {
	refresh(frm) {
		if (frm.doc.crm_pipeline) {
			frm.set_query("opportunity_stage", function (txt) {
				return {
					query: "traffictech.utils.get_opporunity_stages",
					filters: {
						pipeline: frm.doc.crm_pipeline,
					},
				};
			});
		}

		if (!frm.is_new()){
			frm.add_custom_button('Estimation', function() {
				frappe.new_doc("Estimation", {
					"party_type": "Opportunity",
					"party": frm.doc.name,
					"currency": frm.doc.currency,
				})
			}, "Create");
		}
	},
	crm_pipeline: function(frm) {
		if (frm.doc.crm_pipeline) {
			frm.set_query("opportunity_stage", function (txt) {
				return {
					query: "traffictech.utils.get_opporunity_stages",
					filters: {
						pipeline: frm.doc.crm_pipeline,
					},
				};
			});
		}
	},
	opportunity_stage: function(frm) {
		if (frm.doc.opportunity_stage) {
			frappe.call({
				method: "traffictech.utils.get_probability",
				args: { pipeline: frm.doc.crm_pipeline, stage: frm.doc.opportunity_stage},
				callback: function (r) {
					if (r.message) {
						frm.set_value("probability", r.message);
					}
					
				}
			});
		}
	}
});