# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class StudentGrade(Document):
    def validate(self):
        try:
            self.grade = logic.check_grade(self.grade)
        except logic.LogicError as e:
            frappe.throw(str(e))
        class_list = frappe.db.get_value(
            "Class List", self.class_list, ["adviser", "academic_year", "grade_level"], as_dict=True
        )
        # the owning teacher always follows the class list (also used by permission hooks)
        self.teacher = class_list.adviser
        self.academic_year = class_list.academic_year
        self.grade_level = class_list.grade_level
        if not frappe.db.exists("Class List Student", {"parent": self.class_list, "student": self.student}):
            frappe.throw(_("{0} is not in class list {1}.").format(self.student, self.class_list))
        self.student_name = frappe.db.get_value("BEd Student", self.student, "student_name")
