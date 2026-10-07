# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class Applicant(Document):
    def validate(self):
        self.normalize()

    def normalize(self):
        """Clean names/contacts. Bad contact data warns but never blocks the record."""
        for field in ("first_name", "middle_name", "last_name"):
            self.set(field, logic.normalize_name(self.get(field)))
        self.full_name = " ".join(p for p in (self.first_name, self.middle_name, self.last_name) if p)

        if self.email:
            clean = logic.normalize_email(self.email)
            if clean:
                self.email = clean
            else:
                frappe.msgprint(_("Email looks invalid; kept as typed."), indicator="orange", alert=True)
        if self.mobile:
            clean = logic.normalize_mobile(self.mobile)
            if clean:
                self.mobile = clean
            else:
                frappe.msgprint(_("Mobile number is not a valid PH number; kept as typed."), indicator="orange", alert=True)
