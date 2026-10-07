# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AcademicTerm(Document):
    def validate(self):
        if self.max_units is None or self.max_units < 0:
            frappe.throw(_("Max Units cannot be negative."))
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw(_("End Date cannot be before Start Date."))
