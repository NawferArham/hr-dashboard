
frappe.listview_settings["Expense Entry"] = {
    add_fields: [
        "status"
    ],
    onload: function (listview) {
        listview.page.add_inner_button(__("Multi Expense"), function () {
            let d = new frappe.ui.Dialog({
                title: __("Multi Page"),
                fields: [
                    {
                        fieldname: "file_url",
                        label: __("File"),
                        fieldtype: "Attach",
                        reqd: 1,
                    },
                ],
                primary_action(data) {
                    frappe.call({
                        method: "traffictech.traffictech.doctype.expense_entry.expense_entry.create_multi_page_ocr",
                        args: {
                            file_url: data.file_url,
                        },
                        callback: function (r) {
                            console.log(r.message);
                            
                            if (r.message === 1) {
                                // frappe.show_alert({
                                //     message: __("Attendance Marked"),
                                //     indicator: "blue",
                                // });
                                // cur_dialog.hide();
                            }
                        },
                    });

                    d.hide();
                    listview.refresh();
                },
                primary_action_label: __("Create"),
            });
            d.show();
        });
    }

}
