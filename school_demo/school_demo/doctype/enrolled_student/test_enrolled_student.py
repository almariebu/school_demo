# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestEnrolledStudent(FrappeTestCase):
    def test_one_record_per_applicant_and_term(self):
        term = utils.make_term().name
        utils.make_program()
        applicant = utils.make_applicant(email="dup.test@example.ph")
        values = {"doctype": "Enrolled Student", "student_name": "Dup Test", "applicant": applicant.name, "academic_term": term}
        frappe.get_doc(values).insert()
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc(values).insert()
