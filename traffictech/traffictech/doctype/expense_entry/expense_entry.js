// Copyright (c) 2025, Niyaz Razak and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Entry", {
    onload: function (frm) {
        if (!frm.doc.employee) {
            frappe.db.get_value("Employee", { "user_id": frappe.session.user }, "name", (r) => {
                if (r.name) {
                    frm.set_value("employee", r.name);
                }
            })
        }
    },
    refresh: function (frm) {
        frm.trigger("change_form_labels");
        frm.trigger("change_grid_labels");
        // Add a button to trigger OCR processing
        if (!frm.doc.docstatus) {
            frm.add_custom_button(__('Extract Data'), function () {
                get_ocr_document_file(frm);
            });
        }
        if (frm.doc.category) {
            frm.call("check_category");
        }
    },
    file(frm) {
        if (frm.doc.file) {
            get_ocr_document_file(frm);
        }
    },
    currency(frm) {
        frm.trigger("get_exchange_rate");
        frm.trigger("change_form_labels");
        frm.trigger("change_grid_labels");
    },
    conversion_rate(frm) {
        calculate_base_total(frm);
    },
    get_exchange_rate(frm) {
        if (frm.doc.currency != company_currency) {
            var company_currency = erpnext.get_currency(frm.doc.company);
            frappe.call({
                method: "erpnext.setup.utils.get_exchange_rate",
                args: {
                    transaction_date: frm.doc.supplier_invoice_date,
                    from_currency: frm.doc.currency,
                    to_currency: company_currency,
                    args: "for_buying",
                },
                callback: function (r) {
                    const exchange_rate = flt(r.message, 9);
                    frm.set_value("conversion_rate", exchange_rate);
                },
            });
        } else {
            frm.set_value("conversion_rate", 1);
        }
    },
    change_form_labels(frm) {
        var company_currency = erpnext.get_currency(frm.doc.company);
        frm.toggle_display(["conversion_rate"], frm.doc.currency != company_currency)
        frm.toggle_display(["base_total", "base_net_total", "base_tax_and_charges",
            "base_discount_amount", "base_grand_total"],
            frm.doc.currency != company_currency
        );
        frm.set_currency_labels(["base_total", "base_net_total", "base_tax_and_charges",
            "base_discount_amount", "base_grand_total"], company_currency);

        frm.set_currency_labels(["total", "net_total", "tax_and_charges",
            "discount_amount", "grand_total"], frm.doc.currency);
    },
    change_grid_labels(frm) {
        var company_currency = erpnext.get_currency(frm.doc.company);
        var item_grid = frm.fields_dict["items"].grid;
        $.each(["base_rate", "base_amount",], function (i, fname) {
            if (frappe.meta.get_docfield(item_grid.doctype, fname))
                item_grid.set_column_disp(fname, frm.doc.currency != company_currency);
        });
        frm.set_currency_labels(["base_rate", "base_amount"], company_currency, "items");
        frm.set_currency_labels(["rate", "amount"], frm.doc.currency, "items");
    },
    total(frm) {
        calculate_total(frm);
        calculate_base_total(frm);
    },
    net_total(frm) {
        calculate_total(frm);
        calculate_base_total(frm);
    },
    tax_and_charges(frm) {
        calculate_total(frm);
        calculate_base_total(frm);
    },
    discount_amount(frm) {
        calculate_total(frm);
        calculate_base_total(frm);
    },
});

frappe.ui.form.on("Expense Entry Log", {
    qty(frm, cdt, cdn) {
        calculate_total(frm);
        calculate_base_total(frm);
    },
    rate(frm, cdt, cdn) {
        calculate_total(frm);
        calculate_base_total(frm);
    },
})

function get_ocr_document_file(frm) {
    if (!frm.doc.file) {
        frappe.msgprint(__("Please upload a file first."));
        return;
    }

    frm.call({
        method: 'ocr_document_file',
        doc: frm.doc,
        args: {
            file_url: frm.doc.file
        },
        callback: function (r) {
            if (r.message) {
                // Populate the form fields with the extracted data
                frm.set_value('json_data', JSON.stringify(r.message));
                frm.set_value('supplier', r.message.supplier);
                frm.set_value('supplier_invoice_date', r.message.date);
                frm.set_value('supplier_invoice_no', r.message.supplier_invoice_no);
                frm.set_value('currency', r.message.currency);
                frm.set_value('category', r.message.category);
                frm.set_value('items', []);
                var items = r.message.items || [];
                for (let t of items) {
                    let row = frm.add_child("items", {
                        description: t.description,
                        qty: t.qty,
                        rate: t.rate,
                        amount: t.amount,
                    });
                }
                frm.set_value('tax_and_charges', r.message.tax);
                frm.set_value('discount_amount', r.message.discount);
                frm.refresh_field("items");
                calculate_total(frm);
            } else {
                frappe.msgprint(__("Failed to extract data. Please upload a clearer image or PDF."));
            }
        }
    });
}

function calculate_total(frm) {
    $.each(frm.doc.items || [], function (i, d) {
        let amount = flt(d.qty) * flt(d.rate);
        frappe.model.set_value(d.doctype, d.name, 'amount', amount);
    })

    let total_qty = (frm.doc.items || []).reduce((total, d) => total + d.qty, 0);
    frm.set_value("total_qty", total_qty);

    let total = (frm.doc.items || []).reduce((total, d) => total + d.amount, 0);
    frm.set_value("total", total);

    let net_total = flt(frm.doc.total) - flt(frm.doc.discount_amount);
    frm.set_value("net_total", net_total);

    let grand_total = flt(frm.doc.tax_and_charges) + flt(frm.doc.net_total);
    frm.set_value("grand_total", grand_total);
}

function calculate_base_total(frm) {
    var company_currency = erpnext.get_currency(frm.doc.company);
    if (frm.doc.currency != company_currency) {
        $.each(frm.doc.items || [], function (i, d) {
            let base_rate = flt(frm.doc.conversion_rate, 9) * flt(d.rate);
            frappe.model.set_value(d.doctype, d.name, 'base_rate', base_rate);

            let base_amount = flt(d.qty) * flt(d.base_rate);
            frappe.model.set_value(d.doctype, d.name, 'base_amount', base_amount);
        })

        let base_total = (frm.doc.items || []).reduce((total, d) => total + d.base_amount, 0);
        frm.set_value("base_total", base_total);

        let base_discount_amount = flt(frm.doc.conversion_rate, 9) * flt(frm.doc.discount_amount);
        frm.set_value("base_discount_amount", base_discount_amount);

        let base_net_total = flt(frm.doc.base_total) - flt(frm.doc.base_discount_amount);
        frm.set_value("base_net_total", base_net_total);

        let base_tax_and_charges = flt(frm.doc.conversion_rate, 9) * flt(frm.doc.tax_and_charges);
        frm.set_value("base_tax_and_charges", base_tax_and_charges);

        let base_grand_total = flt(frm.doc.base_tax_and_charges) + flt(frm.doc.base_net_total);
        frm.set_value("base_grand_total", base_grand_total);
    }
}