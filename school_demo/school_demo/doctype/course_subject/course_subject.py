# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CourseSubject(Document):
    def validate(self):
        if (self.units or 0) <= 0:
            frappe.throw(_("Units must be greater than zero."))
