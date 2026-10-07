// Copyright (c) 2026, Almarie Bullo and contributors
// For license information, please see license.txt

const BED_ENROLLMENT = "school_demo.school_demo.doctype.bed_enrollment.bed_enrollment";

frappe.ui.form.on("BEd Enrollment", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Active") {
			frm.add_custom_button(__("Withdraw"), () => {
				frappe.prompt(
					[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }],
					(values) => {
						frappe.call({
							method: `${BED_ENROLLMENT}.withdraw`,
							args: { name: frm.doc.name, reason: values.reason },
							freeze: true,
							callback(r) {
								if (!r.message) return;
								frappe.show_alert({
									message: __("Withdrawn. Class lists updated: {0}, grade rows cleared: {1}", [
										r.message.class_lists,
										r.message.student_grades,
									]),
									indicator: "orange",
								});
								frm.reload_doc();
							},
						});
					},
					__("Withdraw Enrollment"),
					__("Withdraw")
				);
			});
		}
		if (frm.doc.status === "Withdrawn") {
			frm.dashboard.set_headline_alert(__("This enrollment was withdrawn on {0}.", [frm.doc.withdrawal_date]), "red");
		}
	},

	student: (frm) => frm.trigger("preview_grade"),
	academic_year: (frm) => frm.trigger("preview_grade"),
	enrollment_type: (frm) => frm.trigger("preview_grade"),
	incoming_grade_level: (frm) => frm.trigger("preview_grade"),

	preview_grade(frm) {
		const d = frm.doc;
		if (frm.doc.docstatus !== 0 || !d.student || !d.academic_year || !d.enrollment_type) return;
		frappe.call({
			method: `${BED_ENROLLMENT}.get_grade_level`,
			args: {
				student: d.student,
				academic_year: d.academic_year,
				enrollment_type: d.enrollment_type,
				incoming_grade_level: d.incoming_grade_level,
			},
			silent: true,
			callback: (r) => r.message && frm.set_value("grade_level", r.message),
		});
	},
});
