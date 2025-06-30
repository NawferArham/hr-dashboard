// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Office QRCode", {
	refresh: function (frm) {
		// frm.disable_save()
		const updateQRCode = () => {
			frm.call({
				method: "generate_qr_code",
				doc: frm.doc,
				callback: function (r) {
					if (r.message && r.message.qr_code) {
						frm.set_value("qrcode_data", r.message.qr_code);
						const qr_code_html = frm.get_field('qrcode').$wrapper;

						qr_code_html.empty();

						var rows = $('<center><div id="qrcode-container"></div></center>').appendTo(qr_code_html);

						var qrcode = new QRCode("qrcode-container", {
							text: r.message.qr_code, // Set the URL or data for QR code
							width: 400, // Set the width of the QR code
							height: 400, // Set the height of the QR code
							colorDark: "#000000", // Dark color for the QR code
							colorLight: "#ffffff", // Light color for the background
							correctLevel: QRCode.CorrectLevel.L // Error correction level
						});

						// Optional: Add additional details to the container
						var details = "<div>Some extra details or context here.</div>";
						$(details).appendTo(rows);

					}
				}
			});
		};
		// Ensure `interval` is valid, default to 3 seconds
		const interval = frm.doc.interval > 0 ? frm.doc.interval * 1000 : 5000;

		// Initial QR code generation
		updateQRCode();

		// Prevent multiple intervals
		if (!frm.qr_interval) {
			frm.qr_interval = setInterval(updateQRCode, interval);
		}
	},
	onhide: function (frm) {
		if (frm.qr_interval) {
			clearInterval(frm.qr_interval);
			frm.qr_interval = null;
		}
	}
});