// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Enrollment Assessment", {
	setup(frm) {
		frm.set_query("class_schedule", "subjects", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return { filters: { academic_term: doc.academic_term, subject: row.subject, docstatus: 1 } };
		});
	},

	refresh(frm) {
		if (frm.is_new()) return;
		const color = { Unpaid: "red", Partial: "orange", "Down Payment Met": "green", "Fully Paid": "green" }[frm.doc.payment_status];
		frm.dashboard.add_indicator(
			__("Paid {0} of {1} required down payment", [
				format_currency(frm.doc.amount_paid),
				format_currency(frm.doc.required_downpayment),
			]),
			color || "gray"
		);
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Student Payment"), () => {
				frappe.new_doc("Student Payment", {
					assessment: frm.doc.name,
					amount: Math.max(frm.doc.required_downpayment - frm.doc.amount_paid, 0),
				});
			}, __("Create"));
		}
	},

	applicant(frm) {
		if (!frm.doc.applicant) return;
		frappe.db.get_value("Applicant", frm.doc.applicant, ["program", "academic_term"]).then(({ message }) => {
			if (message) {
				frm.set_value("program", frm.doc.program || message.program);
				frm.set_value("academic_term", frm.doc.academic_term || message.academic_term);
			}
		});
	},
});
