// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Class List", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.student_count) {
			frm.dashboard.add_indicator(__("{0} students", [frm.doc.student_count]), "blue");
		}
	},
});
