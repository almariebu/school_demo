# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class StudentFee(Document):
    def validate(self):
        if logic.flt(self.amount) <= 0:
            frappe.throw(_("Amount must be greater than zero."))
        if logic.flt(self.paid_amount) > logic.flt(self.amount):
            frappe.throw(_("Paid amount cannot be more than the fee amount."))
        self.balance = logic.fee_balance({"amount": self.amount, "paid": self.paid_amount})
