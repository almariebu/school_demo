frappe.listview_settings["Account Closing"] = {
    add_fields: ["status"],
    get_indicator(doc) {
        const colors = { Draft: "gray", Queued: "orange", Running: "blue", Done: "green", Failed: "red" };
        return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
    },
};
