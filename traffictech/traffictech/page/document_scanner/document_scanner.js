frappe.pages['document-scanner'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Document Scanner',
		single_column: true
	});

	frappe.require(['scanner.bundle.css', 'scanner.bundle.js']).then(() => {
        new traffictech.DocScanner({
            wrapper: $(page.main),
            page: page
        });
	});
}