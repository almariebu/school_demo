# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from school_demo import messaging


class OutgoingMessage(Document):
    def validate(self):
        messaging.prepare(self)
