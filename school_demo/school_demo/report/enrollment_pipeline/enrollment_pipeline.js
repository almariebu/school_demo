// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

frappe.query_reports["Enrollment Pipeline"] = {
	filters: [
		{
			fieldname: "academic_term",
			label: __("Academic Term"),
			fieldtype: "Link",
			options: "Academic Term",
		},
	],
};
