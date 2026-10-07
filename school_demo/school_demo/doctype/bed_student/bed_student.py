# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from school_demo import logic


class BEdStudent(Document):
    def validate(self):
        self.student_name = logic.normalize_name(self.student_name)
        try:
            self.lrn = logic.check_lrn(self.lrn) or None
        except logic.LogicError as e:
            frappe.throw(str(e))
    # Class List / Student Grade names are refreshed by school_demo.events.refresh_student_names (doc_events).
