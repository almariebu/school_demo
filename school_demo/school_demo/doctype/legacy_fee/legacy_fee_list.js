frappe.listview_settings["Legacy Fee"] = {
    add_fields: ["status"],
    get_indicator(doc) {
        return [__(doc.status), doc.status === "Mapped" ? "green" : "red", "status,=," + doc.status];
    },
};
