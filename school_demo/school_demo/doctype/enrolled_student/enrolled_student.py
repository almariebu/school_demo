# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EnrolledStudent(Document):
    def validate(self):
        """One student record per applicant + term (guards against duplicates)."""
        duplicate = frappe.db.exists(
            "Enrolled Student",
            {"applicant": self.applicant, "academic_term": self.academic_term, "name": ["!=", self.name or ""]},
        )
        if duplicate:
            frappe.throw(
                _("{0} is already enrolled for {1} ({2}).").format(self.applicant, self.academic_term, duplicate),
                title=_("Duplicate Enrollment"),
            )
