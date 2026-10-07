// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Applicant", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Enrollment Assessment"), () => {
			frappe.new_doc("Enrollment Assessment", {
				applicant: frm.doc.name,
				academic_term: frm.doc.academic_term,
				program: frm.doc.program,
			});
		}, __("Create"));
		if (frm.doc.student) {
			frm.dashboard.add_indicator(__("Enrolled as {0}", [frm.doc.student]), "green");
		}
	},
});
