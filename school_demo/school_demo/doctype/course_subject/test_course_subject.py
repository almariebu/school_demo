# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestCourseSubject(FrappeTestCase):
    def test_subject_is_named_by_code(self):
        self.assertEqual(utils.make_subject("TST-X1", 2).name, "TST-X1")

    def test_units_must_be_positive(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({"doctype": "Course Subject", "subject_code": "TST-X0", "title": "Zero", "units": 0}).insert()
