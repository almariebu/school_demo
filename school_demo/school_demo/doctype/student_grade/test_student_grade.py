# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo import permissions
from school_demo.tests import utils


class TestStudentGrade(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.teacher1 = utils.make_user("teacher.sg1@example.ph", ["Teacher"]).name
        cls.teacher2 = utils.make_user("teacher.sg2@example.ph", ["Teacher"]).name
        cls.student = utils.make_bed_student("Grade Learner")
        utils.make_bed_enrollment(cls.student.name, "2098-2099", "New", "Grade 11")
        cls.class_list = frappe.get_doc({
            "doctype": "Class List", "class_name": "Grade 11 - SG", "academic_year": "2098-2099", "grade_level": "Grade 11",
            "adviser": cls.teacher1, "students": [{"student": cls.student.name}],
        }).insert()

    def _grade(self, value=90, area="Math"):
        return frappe.get_doc({
            "doctype": "Student Grade", "student": self.student.name, "class_list": self.class_list.name,
            "learning_area": area, "quarter": "Q1", "grade": value,
        }).insert()

    def test_teacher_follows_class_list(self):
        self.assertEqual(self._grade().teacher, self.teacher1)

    def test_grade_range(self):
        with self.assertRaises(frappe.ValidationError):
            self._grade(120)

    def test_teacher_permission_hooks(self):
        grade = self._grade(area="Science")
        self.assertIsNone(permissions.student_grade_has_permission(grade, user=self.teacher1))
        self.assertFalse(permissions.student_grade_has_permission(grade, user=self.teacher2))
        self.assertIn(self.teacher2, permissions.student_grade_query(self.teacher2))
