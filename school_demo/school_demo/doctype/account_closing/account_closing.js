frappe.ui.form.on("Account Closing", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (["Draft", "Failed"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Start closing"), () => {
                frappe.call({
                    method: "school_demo.closing.start_closing",
                    args: { name: frm.doc.name },
                    freeze: true,
                    callback: () => frm.reload_doc(),
                });
            });
        }
        if (["Queued", "Running"].includes(frm.doc.status)) {
            frm.dashboard.set_headline(__("Closing runs in the background. Refresh to see progress."));
        }
    },
});
