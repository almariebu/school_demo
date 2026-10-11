frappe.listview_settings["Enrollment Assessment"] = frappe.listview_settings["Enrollment Assessment"] || {};
const original_onload = frappe.listview_settings["Enrollment Assessment"].onload;
frappe.listview_settings["Enrollment Assessment"].onload = function (listview) {
    if (original_onload) original_onload(listview);
    listview.page.add_action_item(__("Apply discount"), () => {
        const selected = listview.get_checked_items(true);
        if (!selected.length) return frappe.msgprint(__("Select at least one assessment."));
        frappe.prompt(
            [
                { fieldname: "discount_type", fieldtype: "Data", label: __("Discount Type"), reqd: 1 },
                { fieldname: "basis", fieldtype: "Select", label: __("Computed From"), options: "assessment\nbalance", default: "assessment", reqd: 1 },
                { fieldname: "mode", fieldtype: "Select", label: __("Mode"), options: "percent\nfixed", default: "percent", reqd: 1 },
                { fieldname: "value", fieldtype: "Float", label: __("Value"), reqd: 1 },
            ],
            (rule) =>
                frappe.call({
                    method: "school_demo.discounts.apply_discount_batch",
                    args: { rule, assessments: selected },
                    callback: (r) =>
                        frappe.msgprint(__("Added {0}, skipped {1} (already had this discount).", [r.message.added.length, r.message.skipped.length])),
                }),
            __("Apply discount to {0} students", [selected.length])
        );
    });
};
