frappe.ui.form.on("Outgoing Message", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status === "Sent") return;
        frm.add_custom_button(__("Send now"), () => {
            frappe.call({
                method: "school_demo.messaging.send_message",
                args: { name: frm.doc.name },
                callback: () => frm.reload_doc(),
            });
        });
    },
});
