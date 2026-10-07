# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestProgram(FrappeTestCase):
    def test_doctype_is_installed(self):
        self.assertTrue(frappe.db.exists("DocType", "Program"))
