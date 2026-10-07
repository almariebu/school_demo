# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.school_demo.doctype.bed_enrollment.bed_enrollment import withdraw
from school_demo.tests import utils


def make_class_list(grade, year, adviser, students):
    return frappe.get_doc({
        "doctype": "Class List", "class_name": f"{grade} - Test", "academic_year": year, "grade_level": grade,
        "adviser": adviser, "students": [{"student": s} for s in students],
    }).insert()


class TestBEdEnrollment(FrappeTestCase):
    def test_new_student_keeps_incoming_grade(self):
        student = utils.make_bed_student("New Learner")
        enr = utils.make_bed_enrollment(student.name, "2098-2099", "New", "Grade 4", submit=False)
        self.assertEqual(enr.grade_level, "Grade 4")

    def test_continuing_student_moves_up_one_grade(self):
        student = utils.make_bed_student("Continuing Learner")
        utils.make_bed_enrollment(student.name, "2097-2098", "New", "Grade 6")
        enr = utils.make_bed_enrollment(student.name, "2098-2099", "Continuing", None, submit=False)
        self.assertEqual(enr.grade_level, "Grade 7")
        self.assertTrue(enr.last_enrollment)

    def test_kinder_promotes_to_grade_1(self):
        student = utils.make_bed_student("Kinder Learner")
        utils.make_bed_enrollment(student.name, "2097-2098", "New", "Kinder")
        enr = utils.make_bed_enrollment(student.name, "2098-2099", "Continuing", None, submit=False)
        self.assertEqual(enr.grade_level, "Grade 1")

    def test_continuing_without_history_is_blocked(self):
        student = utils.make_bed_student("No History")
        with self.assertRaises(frappe.ValidationError):
            utils.make_bed_enrollment(student.name, "2098-2099", "Continuing", None, submit=False)

    def test_second_active_enrollment_same_year_blocked(self):
        student = utils.make_bed_student("Double Enroll")
        utils.make_bed_enrollment(student.name, "2098-2099", "New", "Grade 2")
        with self.assertRaises(frappe.ValidationError):
            utils.make_bed_enrollment(student.name, "2098-2099", "New", "Grade 2", submit=False)

    def test_can_reenroll_after_withdrawal(self):
        student = utils.make_bed_student("Comes Back")
        enr = utils.make_bed_enrollment(student.name, "2098-2099", "New", "Grade 3")
        withdraw(enr.name, "Moved away")
        again = utils.make_bed_enrollment(student.name, "2098-2099", "New", "Grade 3", submit=False)
        self.assertEqual(again.status, "Active")

    def test_withdraw_clears_class_list_rows(self):
        teacher = utils.make_user("teacher.bed1@example.ph", ["Teacher"]).name
        stay = utils.make_bed_student("Stays")
        leave = utils.make_bed_student("Leaves")
        utils.make_bed_enrollment(stay.name, "2098-2099", "New", "Grade 5")
        enr = utils.make_bed_enrollment(leave.name, "2098-2099", "New", "Grade 5")
        cl = make_class_list("Grade 5", "2098-2099", teacher, [stay.name, leave.name])
        self.assertEqual(cl.student_count, 2)

        result = withdraw(enr.name, "Transferred")
        self.assertEqual(result["class_lists"], 1)
        self.assertEqual(result["student_grades"], 0)  # not senior high
        self.assertEqual(frappe.db.get_value("BEd Enrollment", enr.name, "status"), "Withdrawn")
        cl.reload()
        self.assertEqual([r.student for r in cl.students], [stay.name])

    def test_withdraw_clears_senior_high_grades_only(self):
        teacher = utils.make_user("teacher.bed2@example.ph", ["Teacher"]).name
        for grade, name in (("Grade 11", "SHS Learner"), ("Grade 10", "JHS Learner")):
            student = utils.make_bed_student(name)
            enr = utils.make_bed_enrollment(student.name, "2098-2099", "New", grade)
            cl = make_class_list(grade, "2098-2099", teacher, [student.name])
            frappe.get_doc({
                "doctype": "Student Grade", "student": student.name, "class_list": cl.name,
                "learning_area": "Math", "quarter": "Q1", "grade": 88,
            }).insert()
            result = withdraw(enr.name, "Dropped")
            remaining = frappe.db.count("Student Grade", {"student": student.name})
            if grade == "Grade 11":
                self.assertEqual((result["student_grades"], remaining), (1, 0))
            else:
                self.assertEqual((result["student_grades"], remaining), (0, 1))

    def test_withdraw_twice_blocked(self):
        student = utils.make_bed_student("Withdraw Twice")
        enr = utils.make_bed_enrollment(student.name, "2098-2099", "New", "Grade 8")
        withdraw(enr.name, "x")
        with self.assertRaises(frappe.ValidationError):
            withdraw(enr.name, "y")
