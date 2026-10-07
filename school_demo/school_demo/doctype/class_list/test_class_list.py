# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo import permissions
from school_demo.tests import utils


class TestClassList(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.teacher1 = utils.make_user("teacher.cl1@example.ph", ["Teacher"]).name
        cls.teacher2 = utils.make_user("teacher.cl2@example.ph", ["Teacher"]).name
        cls.student = utils.make_bed_student("Maria Santos")
        utils.make_bed_enrollment(cls.student.name, "2098-2099", "New", "Grade 7")

    def _make(self, adviser, name="Grade 7 - Rizal"):
        return frappe.get_doc({
            "doctype": "Class List", "class_name": name, "academic_year": "2098-2099", "grade_level": "Grade 7",
            "adviser": adviser, "students": [{"student": self.student.name}],
        }).insert()

    def test_student_must_be_actively_enrolled_in_that_grade(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Class List", "class_name": "Grade 9 - X", "academic_year": "2098-2099", "grade_level": "Grade 9",
                "adviser": self.teacher1, "students": [{"student": self.student.name}],
            }).insert()

    def test_current_name_follows_student_rename(self):
        cl = self._make(self.teacher1)
        self.assertEqual(cl.students[0].student_name, "Maria Santos")
        student = frappe.get_doc("BEd Student", self.student.name)
        student.student_name = "Maria Santos-Reyes"
        student.save()  # fires the on_update doc_event
        self.assertEqual(
            frappe.db.get_value("Class List Student", {"parent": cl.name}, "student_name"), "Maria Santos-Reyes"
        )
        # and render time (onload) also reads the master record
        frappe.db.set_value("Class List Student", {"parent": cl.name}, "student_name", "stale")
        cl.reload()
        cl.onload()
        self.assertEqual(cl.students[0].student_name, "Maria Santos-Reyes")

    def test_teacher_query_conditions(self):
        self.assertIn(self.teacher1, permissions.class_list_query(self.teacher1))
        self.assertEqual(permissions.class_list_query("Administrator"), "")

    def test_teacher_sees_only_own_classes(self):
        mine = self._make(self.teacher1, "Grade 7 - Mine")
        theirs = self._make(self.teacher2, "Grade 7 - Theirs")
        visible = frappe.get_list("Class List", filters={"academic_year": "2098-2099"}, pluck="name", user=self.teacher1)
        self.assertIn(mine.name, visible)
        self.assertNotIn(theirs.name, visible)

    def test_has_permission_hook(self):
        mine = self._make(self.teacher1, "Grade 7 - Mine")
        theirs = self._make(self.teacher2, "Grade 7 - Theirs")
        self.assertTrue(frappe.has_permission("Class List", "read", doc=mine, user=self.teacher1))
        self.assertFalse(frappe.has_permission("Class List", "read", doc=theirs, user=self.teacher1))
