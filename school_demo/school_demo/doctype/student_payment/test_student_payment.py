# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestStudentPayment(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.term = utils.make_term().name
        utils.make_program()
        utils.make_subject("TST-S1", 3)
        utils.make_fee_structure(cls.term)
        applicant = utils.make_applicant(email="pay.test@example.ph")
        cls.assessment = utils.make_assessment(applicant.name, cls.term, ["TST-S1"])

    def test_amount_must_be_positive(self):
        with self.assertRaises(frappe.ValidationError):
            utils.make_payment(self.assessment.name, 0)

    def test_submit_and_cancel_change_paid_total(self):
        payment = utils.make_payment(self.assessment.name, 2500)
        self.assertEqual(self.assessment.get_paid_amount(), 2500)
        payment.cancel()
        self.assertEqual(self.assessment.get_paid_amount(), 0)

    def test_rejected_assessment_cannot_receive_payment(self):
        frappe.db.set_value("Enrollment Assessment", self.assessment.name, "workflow_state", "Rejected")
        with self.assertRaises(frappe.ValidationError):
            utils.make_payment(self.assessment.name, 100)
