// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Maintenance Checklist", {
	refresh(frm) {
		frm.set_df_property("main_activities", "cannot_add_rows", true);
		highlight_divider_rows(frm);
	},
	main_activities_on_form_rendered(frm, cdt, cdn) {
		highlight_divider_rows(frm);
	}
});

frappe.ui.form.on("Maintenance Checklist Template Activity", {
	update(frm, cdt, cdn) { 
		let row = locals[cdt][cdn];  // Get the selected parent activity row
		update_activity(frm, row);
	}
});

function update_activity(frm, parent_row) {
	if (parent_row.divider) {
		let d = new frappe.ui.Dialog({
			title: `Update Comments for Template: <b style="color:red;">${parent_row.activity}</b>`,
			size: "large",
			fields: [
				{
					fieldtype: "Small Text",
					fieldname: "comments",
					label: "Comments",
					reqd: 1,
					default: parent_row.comments,
				}
			],
			primary_action_label: "Update",
			primary_action(values) {
				if (values.comments) {
					frappe.model.set_value(parent_row.doctype, parent_row.name, "comments", values.comments)
					d.hide();
					frm.refresh_field("main_activities");
				}
			}
		});
	
		d.show();
		return
	}
	// Get sub-activities related to the parent activity
	let sub_activities = frm.doc.sub_activities.filter(sa => sa.parent_activity === parent_row.activity);

	if (sub_activities.length === 0) {
		frappe.msgprint("No sub-activities found for this activity.");
		return;
	}

	let table_html = `
		<style>
			.table-responsive {
				width: 100%;
				overflow-x: auto; /* Horizontal scrolling on small screens */
			}

			/* Table Styling */
			table {
				width: 100%;
				border-collapse: collapse;
				text-align: center;
				table-layout: auto;
			}

			th, td {
				border: 1px solid #ddd;
				padding: 8px;
				text-align: center;
				vertical-align: middle;
				white-space: nowrap; /* Prevents text wrapping */
			}

			/* Rotated Headers with Proper Alignment */
			.rotate-header {
				writing-mode: vertical-rl; /* Vertical text */
				transform: rotate(180deg);
				text-align: center;
				white-space: nowrap;
				width: 40px;
				padding: 5px;
			}

			/* Adjust row height for better spacing */
			th {
				height: auto;
			}

			/* Styling for Comment Box (Small Textarea) */
			.comments {
				width: 100%;
				height: 50px;
				resize: vertical;
				padding: 5px;
				border: none;
				border-radius: 4px;
			}

			/* Mobile Optimization */
			@media screen and (max-width: 768px) {
				th.rotate-header {
					writing-mode: initial; /* Make headers horizontal on mobile */
					transform: rotate(0deg);
					height: auto;
					padding: 2px;
				}

				table {
					display: block;
					overflow-x: auto; /* Enables scrolling */
					white-space: nowrap;
				}

				td, th {
					min-width: 100px; /* Prevents squeezing of columns */
				}

				.comments {
					min-width: 150px;
				}
			}
		</style>

		<div class="table-responsive">
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>Sub Activity</th>
						<th class="rotate-header">Clean</th>
						<th class="rotate-header">Check</th>
						<th class="rotate-header">Lubricate</th>
						<th class="rotate-header">Replace</th>
						<th class="rotate-header">Expired</th>
						<th class="rotate-header">As Per Diagram</th>
						<th>Comments</th>
					</tr>
				</thead>
			<tbody>
	`;

	sub_activities.forEach(sub => {
		table_html += `
			<tr data-sub-id="${sub.name}">
				<td>${sub.activity}</td>
				<td><input type="checkbox" class="clean" ${sub.clean ? "checked" : ""}></td>
				<td><input type="checkbox" class="check" ${sub.check ? "checked" : ""}></td>
				<td><input type="checkbox" class="lubricate" ${sub.lubricate ? "checked" : ""}></td>
				<td><input type="checkbox" class="replace" ${sub.replace ? "checked" : ""}></td>
				<td><input type="checkbox" class="expired" ${sub.expired ? "checked" : ""}></td>
				<td><input type="checkbox" class="as_per_diagram" ${sub.as_per_diagram ? "checked" : ""}></td>
				<td><textarea class="comments">${sub.comments || ''}</textarea></td>
			</tr>
		`;
	});

	table_html += `</tbody></table></div>`;

	let d = new frappe.ui.Dialog({
		title: `Update Sub-Activities for: <b style="color:red;">${parent_row.activity}</b>`,
		size: "extra-large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "sub_activity_table",
				options: table_html
			}
		],
		primary_action_label: "Update",
		primary_action() {
			const cdt = "Maintenance Checklist Template Sub Activity"
			cur_dialog.$wrapper.find('tr[data-sub-id]').each(function () {
				let sub_id = $(this).attr("data-sub-id");

				let clean = $(this).find(".clean").prop("checked") ? 1 : 0;
				let check = $(this).find(".check").prop("checked") ? 1 : 0;
				let lubricate = $(this).find(".lubricate").prop("checked") ? 1 : 0;
				let replace = $(this).find(".replace").prop("checked") ? 1 : 0;
				let expired = $(this).find(".expired").prop("checked") ? 1 : 0;
				let as_per_diagram = $(this).find(".as_per_diagram").prop("checked") ? 1 : 0;
				let comments = $(this).find(".comments").val();

				// Update the sub-activity in the child table
				frappe.model.set_value(cdt, sub_id, "clean", clean);
				frappe.model.set_value(cdt, sub_id, "check", check);
				frappe.model.set_value(cdt, sub_id, "lubricate", lubricate);
				frappe.model.set_value(cdt, sub_id, "replace", replace);
				frappe.model.set_value(cdt, sub_id, "expired", expired);
				frappe.model.set_value(cdt, sub_id, "as_per_diagram", as_per_diagram);
				frappe.model.set_value(cdt, sub_id, "comments", comments);
				frm.save();
			});

			d.hide();
			frm.refresh_field("sub_activities"); // Refresh sub-activities table
		}
	});

	d.show();
}


function highlight_divider_rows(frm) {
	frm.fields_dict["main_activities"].grid.grid_rows.forEach(row => {
		if (row.doc.divider) {
			// Apply styling to highlight the row
			$(row.wrapper).css({
				"background-color": "#ffeb3b",  // Yellow highlight
				"font-weight": "bold"
			});
		} else {
			// Reset styling for non-divider rows
			$(row.wrapper).css({
				"background-color": "",
				"font-weight": ""
			});
		}
	});
}