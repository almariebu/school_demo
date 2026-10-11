"""Outgoing SMS and email: pick a working sender and un-stick messages.

``send_message`` hands the message to a stand-in transport (a log line). A real
SMS or SMTP client would replace ``_transport`` and nothing else.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

from school_demo import logic

FINANCE_ROLES = ("Finance Officer", "System Manager")


def _senders():
    return frappe.get_all("Message Sender", fields=["name", "channel", "enabled", "is_default"])


def _sender_for(channel):
    """The sender a message of this channel should use when it has none or its own is unusable."""
    senders = _senders()
    if channel == "SMS":
        preferred = frappe.db.get_single_value("School Settings", "preferred_sms_sender")
        return logic.pick_sender(senders, "SMS", preferred)["name"]
    return logic.default_sender(senders, "Email")["name"]


def prepare(doc):
    """validate hook for Outgoing Message: fill the sender, then mark Queued or Stuck."""
    if doc.sender and frappe.db.get_value("Message Sender", doc.sender, "channel") != doc.channel:
        frappe.throw(_("Sender {0} cannot send {1}.").format(doc.sender, doc.channel))
    if not doc.sender:
        try:
            doc.sender = _sender_for(doc.channel)
        except logic.LogicError as e:
            frappe.throw(str(e))
    if doc.status != "Sent":
        doc.status = "Stuck" if logic.is_stuck(doc.status, doc.sender, _senders()) else "Queued"


def _transport(doc):
    frappe.logger("school_demo").info(f"{doc.channel} to {doc.recipient} via {doc.sender}: {doc.body[:60]}")


@frappe.whitelist()
def send_message(name):
    doc = frappe.get_doc("Outgoing Message", name)
    doc.check_permission("write")
    if doc.status == "Sent":
        return doc.status
    if doc.status == "Stuck":
        frappe.throw(_("This message is stuck: its sender is disabled or missing. Re-route stuck messages first."))
    _transport(doc)
    doc.db_set({"status": "Sent", "sent_on": now_datetime()})
    return "Sent"


@frappe.whitelist()
def reroute_stuck():
    """Point every unsent message at a working sender. Runs hourly and from the desk."""
    frappe.only_for(FINANCE_ROLES)
    senders = _senders()
    fixed = 0
    for row in frappe.get_all("Outgoing Message", filters={"status": ["!=", "Sent"]}, fields=["name", "channel", "sender", "status"]):
        if not logic.is_stuck(row.status, row.sender, senders):
            if row.status == "Stuck":  # its sender was re-enabled
                frappe.db.set_value("Outgoing Message", row.name, "status", "Queued")
            continue
        try:
            sender = _sender_for(row.channel)
        except logic.LogicError:
            frappe.log_error(title=f"School Demo: no sender to re-route {row.name}")
            continue
        frappe.db.set_value("Outgoing Message", row.name, {"sender": sender, "status": "Queued"})
        fixed += 1
    return fixed
