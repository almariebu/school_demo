// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Class Schedule", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.dashboard.set_headline_alert(
				__("Submitted, but day, time, room and instructor can still be edited, then use Update."),
				"blue"
			);
		}
	},
});
