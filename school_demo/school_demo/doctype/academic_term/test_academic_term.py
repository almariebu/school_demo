# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestAcademicTerm(FrappeTestCase):
    def test_name_combines_year_and_semester(self):
        term = utils.make_term(school_year="2098-2099", semester="2nd Semester")
        self.assertEqual(term.name, "2098-2099 2nd Semester")

    def test_negative_max_units_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({"doctype": "Academic Term", "school_year": "2097-2098", "semester": "Summer", "max_units": -1}).insert()
