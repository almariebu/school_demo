# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class StudentPayment(Document):
    def validate(self):
        if logic.flt(self.amount) <= 0:
            frappe.throw(_("Amount must be greater than zero."))
        state = frappe.db.get_value(
            "Enrollment Assessment", self.assessment, ["docstatus", "workflow_state"], as_dict=True
        )
        if state and (state.docstatus == 2 or state.workflow_state == "Rejected"):
            frappe.throw(_("Cannot receive payment for a cancelled or rejected assessment."))

    def on_submit(self):
        self._note(_("Payment {0} of {1} received.").format(self.name, frappe.format(self.amount, {"fieldtype": "Currency"})))

    def on_cancel(self):
        self._note(_("Payment {0} was cancelled.").format(self.name))

    def _note(self, text):
        frappe.get_doc("Enrollment Assessment", self.assessment).add_comment("Info", text)
