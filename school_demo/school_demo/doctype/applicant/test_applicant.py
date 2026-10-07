# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestApplicant(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        utils.make_term()
        utils.make_program()

    def test_names_and_contacts_are_normalized(self):
        doc = utils.make_applicant(
            first="JUAN MIGUEL", last="dela cruz", email="  JUAN@Example.PH ", mobile="0917 123 4567"
        )
        self.assertEqual(doc.full_name, "Juan Miguel Dela Cruz")
        self.assertEqual(doc.mobile, "+639171234567")
        self.assertEqual(doc.email, "juan@example.ph")

    def test_bad_mobile_does_not_block_saving(self):
        doc = utils.make_applicant(email="badmobile.test@example.ph", mobile="not a number")
        self.assertTrue(frappe.db.exists("Applicant", doc.name))
        self.assertEqual(doc.mobile, "not a number")
