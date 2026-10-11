# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from school_demo import logic


class CashCount(Document):
    def validate(self):
        expected = frappe.db.sql(
            "select coalesce(sum(amount), 0) from `tabStudent Payment` "
            "where docstatus = 1 and posting_date = %s and received_by = %s",
            (self.count_date, self.cashier),
        )[0][0]
        result = logic.reconcile(expected, self.counted)
        self.expected, self.variance, self.status = result["expected"], result["variance"], result["status"]
