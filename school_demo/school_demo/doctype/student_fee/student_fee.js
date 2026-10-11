frappe.ui.form.on("Student Fee", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.balance) return;
        frm.add_custom_button(__("Payment link"), () => {
            frappe.call({
                method: "school_demo.api.payment_link",
                args: { fee: frm.doc.name },
                callback: (r) => frappe.msgprint(`<a href="${r.message}" target="_blank" rel="noopener">${r.message}</a>`),
            });
        });
        frm.add_custom_button(__("Simulate gateway payment"), () =>
            frappe.prompt({ fieldname: "amount", fieldtype: "Currency", label: __("Amount"), reqd: 1, default: frm.doc.balance },
                (v) => {
                    frappe.call({
                        method: "school_demo.api.simulate_payment",
                        args: { student: frm.doc.student, amount: v.amount },
                        callback: () => frm.reload_doc(),
                    });
                }, __("Simulate gateway payment"))
        );
    },
});
