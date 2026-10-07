# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.enrollment import enroll_from_assessment
from school_demo.tests import utils


class TestEnrollmentAssessment(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.term = utils.make_term(max_units=9).name
        utils.make_program()
        for code in ("TST-S1", "TST-S2", "TST-S3", "TST-S4"):
            utils.make_subject(code, units=3)
        utils.make_fee_structure(cls.term, tuition_per_unit=500, downpayment=5000)
        cls.applicant = utils.make_applicant(email="assess.test@example.ph")

    def test_totals_are_computed_server_side(self):
        doc = utils.make_assessment(self.applicant.name, self.term, ["TST-S1", "TST-S2"])
        self.assertEqual(doc.total_units, 6)
        self.assertEqual(doc.tuition_total, 3000)
        self.assertEqual(doc.misc_total, 500)
        self.assertEqual(doc.total_fees, 3500)
        self.assertEqual(doc.required_downpayment, 5000)
        self.assertEqual(len(doc.fees), 3)  # tuition + 2 misc

    def test_unit_limit_blocks_save(self):
        with self.assertRaises(frappe.ValidationError):
            utils.make_assessment(self.applicant.name, self.term, ["TST-S1", "TST-S2", "TST-S3", "TST-S4"])

    def test_exactly_at_limit_is_allowed(self):
        doc = utils.make_assessment(self.applicant.name, self.term, ["TST-S1", "TST-S2", "TST-S3"])
        self.assertEqual(doc.total_units, 9)

    def test_client_units_are_ignored(self):
        doc = frappe.get_doc({
            "doctype": "Enrollment Assessment", "applicant": self.applicant.name, "academic_term": self.term,
            "subjects": [{"subject": "TST-S1", "units": 1}],
        }).insert()
        self.assertEqual(doc.subjects[0].units, 3)

    def test_payment_gate(self):
        doc = utils.make_assessment(self.applicant.name, self.term, ["TST-S1"])
        with self.assertRaises(frappe.ValidationError):
            doc.check_payment()

        utils.make_payment(doc.name, 1000)
        with self.assertRaises(frappe.ValidationError):
            doc.check_payment()  # still below the 5,000 requirement
        self.assertEqual(doc.payment_status, "Partial")

        utils.make_payment(doc.name, 4000)
        doc.check_payment()  # passes now
        self.assertEqual(doc.amount_paid, 5000)
        # one subject costs 2,000 in total, so 5,000 also covers the full fees
        self.assertEqual(doc.payment_status, "Fully Paid")

    def test_finance_enroll_action_respects_payment_gate(self):
        from frappe.model.workflow import apply_workflow

        utils.make_user("finance.test@example.ph", ["Finance Officer"])
        doc = utils.make_assessment(self.applicant.name, self.term, ["TST-S1"])
        frappe.db.set_value("Enrollment Assessment", doc.name, "workflow_state", "Pending Finance")
        doc.reload()
        self.addCleanup(frappe.set_user, "Administrator")
        frappe.set_user("finance.test@example.ph")

        with self.assertRaises(frappe.ValidationError):
            apply_workflow(doc, "Enroll")
        self.assertEqual(frappe.db.get_value("Enrollment Assessment", doc.name, "docstatus"), 0)

        frappe.set_user("Administrator")
        utils.make_payment(doc.name, 5000)
        doc.reload()
        frappe.set_user("finance.test@example.ph")
        apply_workflow(doc, "Enroll")
        self.assertEqual(
            frappe.db.get_value("Enrollment Assessment", doc.name, ["docstatus", "workflow_state"]), (1, "Enrolled")
        )

    def test_unsubmitted_payment_does_not_count(self):
        doc = utils.make_assessment(self.applicant.name, self.term, ["TST-S1"])
        utils.make_payment(doc.name, 6000, submit=False)
        with self.assertRaises(frappe.ValidationError):
            doc.check_payment()

    def test_enrollment_is_idempotent(self):
        doc = utils.make_assessment(self.applicant.name, self.term, ["TST-S1"])
        first = enroll_from_assessment(doc)
        second = enroll_from_assessment(doc)
        self.assertEqual(first, second)
        self.assertEqual(
            frappe.db.count("Enrolled Student", {"applicant": self.applicant.name, "academic_term": self.term}), 1
        )

    def test_reenrollment_does_not_wipe_student(self):
        applicant = utils.make_applicant(
            first="ana", last="reyes", email="ana.test@example.ph", mobile="09171234567", gender="Female"
        )
        doc = utils.make_assessment(applicant.name, self.term, ["TST-S1"])
        name = enroll_from_assessment(doc)
        self.assertEqual(frappe.db.get_value("Enrolled Student", name, "mobile"), "+639171234567")

        # the applicant record later gets damaged; enrolling again must keep the good data
        frappe.db.set_value("Applicant", applicant.name, {"mobile": "garbage", "gender": ""})
        self.assertEqual(enroll_from_assessment(doc), name)
        student = frappe.get_doc("Enrolled Student", name)
        self.assertEqual(student.mobile, "+639171234567")
        self.assertEqual(student.gender, "Female")
        self.assertEqual(student.student_name, "Ana Reyes")
