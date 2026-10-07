# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestBEdStudent(FrappeTestCase):
    def test_name_is_normalized(self):
        self.assertEqual(utils.make_bed_student("  jose   RIZAL ").student_name, "Jose Rizal")

    def test_lrn_must_be_12_digits(self):
        with self.assertRaises(frappe.ValidationError):
            utils.make_bed_student("Bad LRN", lrn="123")
        self.assertEqual(utils.make_bed_student("Good LRN", lrn="123456789012").lrn, "123456789012")
