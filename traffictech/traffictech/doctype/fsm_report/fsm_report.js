// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("FSM Report", {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("View Report"), function(){
				open_url_post("/api/method/frappe.utils.print_format.download_pdf", {
					doctype: frm.doc.doctype,
					name: frm.doc.name
				}, 1);
			
			});
		}
	},
	attach_images: function(frm) {
		open_image_dialog(frm);
	}
});

function open_image_dialog(frm, fieldname="attachments") {
	let dialog;

	let image_rows = (frm.doc[fieldname] || []).map(row => ({
		image: row.image,
	}));

	dialog = new frappe.ui.Dialog({
		title: `Attach Images`,
		fields: [
			{
				label: 'Images',
				fieldname: 'images',
				fieldtype: 'Table',
				cannot_add_rows: true,
				in_place_edit: false,
				fields: [
					{
						fieldtype: 'Attach Image',
						fieldname: 'image',
						label: 'Image',
						reqd: 1,
						in_list_view: 1
					},
				]
			},
			{
				fieldtype: 'Section Break',
				fieldname: 'section_brk',
			},
			{
				fieldtype: 'Button',
				label: 'Upload Images',
				fieldname: 'upload_images',
				click: () => {
					new frappe.ui.FileUploader({
						allow_multiple: true,
						on_success(file) {
							image_rows.push({
								image: file.file_url,
								caption: file.name
							});
							dialog.set_value('images', image_rows);
							dialog.fields_dict.images.df.data = image_rows;
							dialog.fields_dict.images.grid.refresh();
						}
					});
				}
			},
			{
				fieldtype: 'Column Break',
				fieldname: 'column_brk',
			},
			{
				fieldtype: 'Button',
				label: 'View Images',
				fieldname: 'view_images',
				click: () => {
					if (!image_rows.length) {
						frappe.msgprint('No images uploaded yet.');
						return;
					}
			
					const wrapper_id = `img-dialog-${Math.random().toString(36).substring(2, 10)}`;
					const wrapper = $(`
						<div id="${wrapper_id}" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; padding: 12px; max-height: 80vh; overflow-y: auto;">
							${image_rows.map((img, index) => `
								<div style="position: relative; border: 1px solid #ccc; padding: 8px; border-radius: 6px; background: #fff;">
									<img 
										src="${img.image}" 
										style="width: 100%; max-height: 500px; object-fit: contain; border-radius: 4px; transition: transform 0.3s ease;" 
										data-index="${index}" 
										data-rotation="0"
									/>
									<button class="rotate-btn" 
										data-target-index="${index}" 
										style="position: absolute; top: 10px; right: 10px; background: #fff; border: 1px solid #ccc; border-radius: 4px; padding: 4px; cursor: pointer;">
										⤾ Rotate
									</button>
								</div>
							`).join("")}
						</div>
					`);
			
					const sub_dialog = new frappe.ui.Dialog({
						title: `Images`,
						fields: [
							{
								fieldtype: 'HTML',
								fieldname: 'image_html',
								options: wrapper.prop('outerHTML')
							}
						],
						size: 'extra-large'
					});
			
					sub_dialog.show();
			
					setTimeout(() => {
						$(`#${wrapper_id} .rotate-btn`).on('click', function () {
							const index = $(this).data('target-index');
							const img = $(`#${wrapper_id} img[data-index="${index}"]`);
							let current = parseInt(img.attr('data-rotation') || 0);
							const next = (current + 90) % 360;
							img.css('transform', `rotate(${next}deg)`);
							img.attr('data-rotation', next);
						});
					
						// Add Save Button after images
						const saveBtn = $(`
							<div style="margin-top: 20px; text-align: center;">
								<button class="btn btn-primary save-rotated-images">Save Rotated Images</button>
							</div>
						`);
						$(`#${wrapper_id}`).after(saveBtn);
					
						$('.save-rotated-images').on('click', function () {
							const promises = [];
					
							$(`#${wrapper_id} img`).each(function () {
								const img = $(this);
								const rotation = parseInt(img.attr('data-rotation') || 0);
								const index = parseInt(img.attr('data-index'));
					
								// Only save if rotated
								if (rotation !== 0) {
									const tempImage = new Image();
									tempImage.crossOrigin = "anonymous";
									tempImage.src = img.attr('src');
					
									const p = new Promise((resolve, reject) => {
										tempImage.onload = function () {
											const canvas = document.createElement('canvas');
											const ctx = canvas.getContext('2d');

											const maxWidth = 1024;
											const maxHeight = 1024;

											let width = tempImage.width;
											let height = tempImage.height;

											if (width > maxWidth || height > maxHeight) {
												const ratio = Math.min(maxWidth / width, maxHeight / height);
												width = width * ratio;
												height = height * ratio;
											}
																
											canvas.width = rotation % 180 === 0 ? width : height;
											canvas.height = rotation % 180 === 0 ? height : width;
					
											ctx.translate(canvas.width / 2, canvas.height / 2);
											ctx.rotate(rotation * Math.PI / 180);
											ctx.drawImage(tempImage, -width / 2, -height / 2, width, height);
					
											canvas.toBlob(blob => {
												const file = new File([blob], `rotated_${Date.now()}.png`, { type: 'image/png' });

												const reader = new FileReader();
												reader.onload = function(event) {
													const base64 = event.target.result.split(',')[1];
											
													frm.call({
														method: "replace_existing_file",
														doc: frm.doc,
														args: {
															file_url: image_rows[index].image,  // Existing image URL
															filedata_base64: base64,
														},
														callback: (r) => {
															if (!r.exc) {
																frappe.msgprint('Image replaced successfully.');
																resolve();
															} else {
																reject(r.exc);
															}
														}
													});
												};
												reader.readAsDataURL(file);
											}, 'image/png');
										};
									});
					
									promises.push(p);
								}
							});
					
							Promise.all(promises)
								.then(() => {
									sub_dialog.set_value('images', image_rows);
									sub_dialog.fields_dict.images.df.data = image_rows;
									sub_dialog.fields_dict.images.grid.refresh();
									frappe.msgprint('All rotated images saved!');
									sub_dialog.hide()
									dialog.hide()
								})
								.catch(err => {
									console.error(err);
									sub_dialog.hide()
								});
						});
					}, 200);
				}
			}
				
		],
		primary_action_label: 'Save',
		primary_action(values) {
			// Clear existing child table
			frm.clear_table(fieldname);

			// Push updated rows to the child table
			(values.images || []).forEach(row => {
				frm.add_child(fieldname, {
					image: row.image,
				});
			});

			frm.refresh_field(fieldname);
			dialog.hide();
		}
	});

	// Set initial data into dialog table
	dialog.set_value('images', image_rows);
	dialog.fields_dict.images.df.data = image_rows;
	dialog.fields_dict.images.grid.refresh();
	dialog.show();
}


frappe.ui.form.on("FSM Report Attachment", {
	preview: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.image) {
			frappe.msgprint("No image to preview.");
			return;
		}

		frappe.msgprint({
			title: 'Image Preview',
			indicator: 'blue',
			message: `<div style="text-align:center">
						<img src="${row.image}" style="max-width:100%; max-height:auto; border:1px solid #ddd;"/>
						</div>`,
			wide: true
		});
	}
});
