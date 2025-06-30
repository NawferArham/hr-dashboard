// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Preventive Maintenance", {
	refresh(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Checklist'), function () {
				frappe.db.get_value("Maintenance Checklist", { "preventive_maintenance": frm.doc.name}, ["name"])
				.then(function (r) {
					if (!r.message.name) {
						frm.call({
							method: "create_checklist",
							doc: frm.doc,
							callback: function (res) {		
								var doc = frappe.model.sync(res.message)				
								frappe.set_route("Form", doc[0].doctype, doc[0].name);
							},
						});
					} else {
						frappe.set_route("Form", "Maintenance Checklist", r.message.name);
					}
				})
			}, 'Create');
		}

		if (frm.doc.tasks.length > 0) {
			frm.add_custom_button('Tasks', function() {
				let task_names = frm.doc.tasks.map(row => row.task);
				frappe.set_route('List', 'Task', { name: ['in', task_names] });
			}, "View");
		}

		if (frm.doc.after && frm.doc.during && frm.doc.after) {
			frm.add_custom_button(__("Final Report"), function(){
				window.open(`/api/method/traffictech.utils.download_pm_final_report?doctype=${frm.doc.doctype}&docname=${frm.doc.name}`);
			});
		}
		
		if (!frm.is_new()) {
			frm.trigger("show_image_download_option");
		}
	},

	before_button: function(frm) {
		open_image_dialog("Before", "before", frm)
	},

	during_button: function(frm) {
		open_image_dialog("During", "during", frm)
	},

	after_button: function(frm) {
		open_image_dialog("After", "after", frm)
	}, 

	additional_button: function(frm) {
		open_image_dialog("Additional", "additional_image", frm)
	},

	show_image_download_option: function(frm) {
		frm.add_custom_button(__('Download Images'), () => {
			frappe.require([
				"https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js",
				"https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"
			], () => {
				const sections = [
					{ label: "Before", fieldname: "before" },
					{ label: "During", fieldname: "during" },
					{ label: "After", fieldname: "after" },
					{ label: "Additional", fieldname: "additional_image" },
				];
			
				const wrapper_id = `download-img-${Math.random().toString(36).substring(2, 10)}`;
				let selectedImages = [];
			
				const buildSection = (label, images, sectionId) => {
					if (!images || !images.length) return '';
					return `
						<div style="margin-bottom: 24px;">
							<h4>${label}</h4>
							<div id="${sectionId}" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
								${images.map((img, i) => `
									<div style="border: 1px solid #ccc; padding: 8px; border-radius: 6px; position: relative; background: #f9f9f9;">
										<img src="${img.image}" 
											style="width: 100%; max-height: 300px; object-fit: contain; border-radius: 4px; margin-bottom: 8px;" 
											alt="Image ${i + 1}" />
										<label style="display: flex; align-items: center; gap: 6px;">
											<input type="checkbox" class="download-check" value="${img.image}" />
											Select
										</label>
										<a href="${img.image}" target="_blank" style="position: absolute; top: 8px; right: 10px; font-size: 12px;">Preview</a>
									</div>
								`).join('')}
							</div>
						</div>
					`;
				};
			
				const getHtml = () => {
					return sections.map(sec => buildSection(sec.label, frm.doc[sec.fieldname], `${wrapper_id}-${sec.fieldname}`)).join('');
				};
			
				const dialog = new frappe.ui.Dialog({
					title: "Download Images",
					fields: [
						{
							fieldtype: 'HTML',
							fieldname: 'image_selector',
							options: `<div id="${wrapper_id}" style="max-height: 70vh; overflow-y: auto;">${getHtml()}</div>`
						},
						{
							fieldtype: 'Section Break'
						},
						{
							fieldtype: 'Column Break'
						},
						{
							fieldtype: 'Check',
							label: 'Select All Images',
							fieldname: 'select_all_images',
							default: 0,
							onchange: function() {
								const checked = this.get_value();
								$(`#${wrapper_id} .download-check`).prop('checked', checked);
							}
						},
						{
							fieldtype: 'Column Break'
						},
						{
							fieldtype: 'Button',
							label: 'Download Selected Images',
							click: () => {
								const checks = $(`#${wrapper_id} .download-check:checked`);
								if (!checks.length) {
									frappe.msgprint("Please select at least one image to download.");
									return;
								}
					
								const urls_by_section = { Before: [], During: [], After: [], Additional: [] };

								[...checks].forEach(input => {
									const url = input.value;
									const parentDiv = $(input).closest('div[id^="' + wrapper_id + '-"]');
									const sectionId = parentDiv.attr('id') || '';
									if (sectionId.includes('before')) {
										urls_by_section.Before.push(url);
									} else if (sectionId.includes('during')) {
										urls_by_section.During.push(url);
									} else if (sectionId.includes('after')) {
										urls_by_section.After.push(url);
									} 
									else if (sectionId.includes('additional_image')) {
										urls_by_section.Additional.push(url);
									}
								});
								
								downloadImagesAsZip(urls_by_section);
							}
						}
					],
					
					size: 'extra-large'
				});
			
				dialog.show();
			
				function downloadImagesAsZip(urls_by_section) {
					const zip = new JSZip();
				
					let totalImages = 0;
					Object.keys(urls_by_section).forEach(section => {
						totalImages += urls_by_section[section].length;
					});
				
					let completed = 0;
					frappe.show_progress("Preparing download", 0, totalImages);
				
					const fetchPromises = [];
				
					Object.entries(urls_by_section).forEach(([section, urls]) => {
						const folder = zip.folder(section);  // Create folder per section
						urls.forEach(url => {
							const promise = fetch(url)
								.then(res => res.blob())
								.then(blob => {
									const originalName = getFileNameFromURL(url);
									folder.file(originalName, blob);
									completed++;
									frappe.show_progress("Preparing download", completed, totalImages);
								});
							fetchPromises.push(promise);
						});
					});
				
					Promise.all(fetchPromises).then(() => {
						const zipName = `images_${frm.doc.name}.zip`;
						zip.generateAsync({ type: "blob" }).then(content => {
							saveAs(content, zipName);
							frappe.hide_progress();
							dialog.hide();
						});
					});
				}

				function getFileNameFromURL(url) {
					const parts = url.split('/');
					return decodeURIComponent(parts[parts.length - 1].split('?')[0]);
				}
			});
		});
	}
});


function open_image_dialog(section, fieldname, frm) {
	let dialog;

	let image_rows = (frm.doc[fieldname] || []).map(row => ({
		image: row.image,
	}));

	dialog = new frappe.ui.Dialog({
		title: `Attach ${section} Images`,
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
					const remaining = 4 - image_rows.length;
					if (remaining <= 0 && fieldname !== "additional_image") {
						frappe.msgprint(`You can only upload up to 4 images for ${section}.`);
						return;
					}

					new frappe.ui.FileUploader({
						allow_multiple: true,
						max_count: remaining,
						on_success(file) {
							image_rows.push({
								image: file.file_url,
								caption: file.name
							});
							dialog.set_value('images', image_rows);
							dialog.fields_dict.images.df.data = image_rows;
							dialog.fields_dict.images.grid.refresh();

							if (image_rows.length > 4 && fieldname !== "additional_image") {
								frappe.throw(`${section} image limit reached (4).`);
								return;
							}
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
						title: `${section} Images`,
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



function setupImagePreview(childTable) {
	frappe.ui.form.on(childTable, {
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
}

// Register for all related child tables
['Preventive Maintenance Before', 'Preventive Maintenance After', 'Preventive Maintenance During', 'Preventive Maintenance Additional']
	.forEach(setupImagePreview);