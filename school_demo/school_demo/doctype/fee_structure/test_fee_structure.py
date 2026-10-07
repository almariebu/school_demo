# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


class TestFeeStructure(FrappeTestCase):
    def test_total_misc_is_computed(self):
        term = utils.make_term().name
        fs = utils.make_fee_structure(term, misc=(("A", 100), ("B", 250.5)))
        self.assertEqual(fs.total_misc, 350.5)

    def test_negative_fee_rejected(self):
        term = utils.make_term().name
        with self.assertRaises(frappe.ValidationError):
            utils.make_fee_structure(term, misc=(("Bad", -1),))
