# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class FeeStructure(Document):
    def validate(self):
        if logic.flt(self.tuition_per_unit) < 0 or logic.flt(self.required_downpayment) < 0:
            frappe.throw(_("Tuition and down payment cannot be negative."))
        for row in self.misc_fees:
            if logic.flt(row.amount) < 0:
                frappe.throw(_("Row {0}: fee amount cannot be negative.").format(row.idx))
        self.total_misc = logic.compute_fee_totals(0, 0, [r.amount for r in self.misc_fees])["misc_total"]
