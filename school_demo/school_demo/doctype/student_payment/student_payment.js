// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Payment", {
	setup(frm) {
		frm.set_query("assessment", () => ({ filters: { docstatus: ["<", 2], workflow_state: ["!=", "Rejected"] } }));
	},
});
