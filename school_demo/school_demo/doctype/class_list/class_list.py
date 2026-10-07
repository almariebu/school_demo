# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ClassList(Document):
    def onload(self):
        """Render time: always show the student's CURRENT name from the master record."""
        self.refresh_student_names()

    def validate(self):
        seen = set()
        for row in self.students:
            if row.student in seen:
                frappe.throw(_("Row {0}: {1} is listed twice.").format(row.idx, row.student))
            seen.add(row.student)
            row.enrollment = frappe.db.get_value(
                "BEd Enrollment",
                {
                    "student": row.student,
                    "academic_year": self.academic_year,
                    "grade_level": self.grade_level,
                    "status": "Active",
                    "docstatus": 1,
                },
            )
            if not row.enrollment:
                frappe.throw(
                    _("Row {0}: {1} has no active {2} enrollment for {3}.").format(
                        row.idx, row.student, self.grade_level, self.academic_year
                    )
                )
        self.refresh_student_names()
        self.student_count = len(self.students)

    def refresh_student_names(self):
        ids = [r.student for r in self.students if r.student]
        if not ids:
            return
        current = dict(frappe.get_all("BEd Student", filters={"name": ["in", ids]}, fields=["name", "student_name"], as_list=True))
        for row in self.students:
            row.student_name = current.get(row.student, row.student_name)
