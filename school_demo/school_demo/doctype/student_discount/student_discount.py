# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class StudentDiscount(Document):
    def validate(self):
        if frappe.db.exists(
            "Student Discount",
            {"assessment": self.assessment, "discount_type": self.discount_type, "name": ["!=", self.name]},
        ):
            frappe.throw(_("{0} already has a {1} discount this term.").format(self.assessment, self.discount_type))
        total, paid = frappe.db.get_value("Enrollment Assessment", self.assessment, ["total_fees", "amount_paid"])
        try:
            self.amount = logic.discount_amount(self.basis, self.mode, self.value, total, paid)
        except logic.LogicError as e:
            frappe.throw(str(e))
