frappe.listview_settings["Outgoing Message"] = {
    add_fields: ["status"],
    get_indicator(doc) {
        const colors = { Queued: "orange", Stuck: "red", Sent: "green" };
        return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
    },
};
