# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MessageSender(Document):
    def validate(self):
        if self.is_default and not self.enabled:
            frappe.throw(_("A default sender must be enabled."))

    def on_update(self):
        if self.is_default:  # one default per channel
            frappe.db.sql(
                "update `tabMessage Sender` set is_default = 0 where channel = %s and name != %s",
                (self.channel, self.name),
            )
