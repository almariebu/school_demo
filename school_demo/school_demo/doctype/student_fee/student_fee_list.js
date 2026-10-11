frappe.listview_settings["Student Fee"] = {
    add_fields: ["balance", "paid_amount"],
    get_indicator(doc) {
        if (!doc.balance) return [__("Paid"), "green", "balance,=,0"];
        if (doc.paid_amount) return [__("Partly paid"), "orange", "balance,>,0"];
        return [__("Unpaid"), "red", "paid_amount,=,0"];
    },
};
