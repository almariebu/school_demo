import json

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo import api, logic


class TestOnlinePayments(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.student = frappe.db.get_value("Enrolled Student", {}, "name")
        assert cls.student, "run the demo seed first: bench execute school_demo.setup.demo_data.seed"
        settings = frappe.get_single("School Settings")
        settings.webhook_secret = "test-secret"
        settings.save(ignore_permissions=True)

    def setUp(self):
        frappe.db.delete("Student Fee", {"student": self.student})
        frappe.db.delete("Online Payment", {"student": self.student})
        for label, due, amount in [("Later", "2026-09-01", 3000), ("Earlier", "2026-08-01", 5000)]:
            frappe.get_doc({"doctype": "Student Fee", "student": self.student, "fee_label": label,
                            "due_date": due, "amount": amount}).insert()

    def _post(self, reference, amount, signature=None):
        body = json.dumps({"reference": reference, "student": self.student, "amount": amount}).encode()
        return api.process_webhook(body, signature or logic.sign_payload("test-secret", body))

    def _paid(self):
        return dict(frappe.get_all("Student Fee", {"student": self.student}, ["fee_label", "paid_amount"], as_list=True))

    def test_bad_signature_is_rejected(self):
        with self.assertRaises(frappe.AuthenticationError):
            self._post("R-BAD", 100, signature="0" * 64)
        self.assertFalse(frappe.db.exists("Online Payment", "R-BAD"))

    def test_applies_oldest_fee_first_and_keeps_credit(self):
        result = self._post("R-1", 6000)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self._paid(), {"Earlier": 5000, "Later": 1000})
        self._post("R-2", 5000)
        self.assertEqual(self._paid(), {"Earlier": 5000, "Later": 3000})
        self.assertEqual(frappe.db.get_value("Online Payment", "R-2", "credit"), 3000)

    def test_repeated_delivery_is_a_no_op(self):
        self._post("R-3", 4000)
        again = self._post("R-3", 4000)
        self.assertEqual(again["status"], "duplicate")
        self.assertEqual(self._paid(), {"Earlier": 4000, "Later": 0})

    def test_simulated_gateway_goes_through_the_webhook(self):
        result = api.simulate_payment(self.student, 1000)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self._paid()["Earlier"], 1000)
