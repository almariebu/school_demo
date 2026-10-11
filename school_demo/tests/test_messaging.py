import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo import messaging


def _sender(name, channel, enabled, default=0):
    return frappe.get_doc({"doctype": "Message Sender", "sender_name": name, "channel": channel,
                           "enabled": enabled, "is_default": default}).insert()


def _message(channel, **kw):
    return frappe.get_doc({"doctype": "Outgoing Message", "channel": channel, "recipient": "x@example.ph",
                           "body": "Hello", **kw}).insert()


class TestMessaging(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.db.delete("Outgoing Message")
        frappe.db.delete("Message Sender")
        _sender("T-old-sms", "SMS", 0)
        _sender("T-new-sms", "SMS", 1)
        _sender("T-old-mail", "Email", 0)
        _sender("T-mail", "Email", 1, default=1)
        frappe.db.set_single_value("School Settings", "preferred_sms_sender", "T-old-sms")

    def test_sms_falls_back_when_preferred_provider_is_disabled(self):
        self.assertEqual(_message("SMS").sender, "T-new-sms")

    def test_email_on_disabled_account_is_stuck_then_rerouted(self):
        msg = _message("Email", sender="T-old-mail")
        self.assertEqual(msg.status, "Stuck")
        with self.assertRaises(frappe.ValidationError):
            messaging.send_message(msg.name)
        self.assertEqual(messaging.reroute_stuck(), 1)
        msg.reload()
        self.assertEqual((msg.sender, msg.status), ("T-mail", "Queued"))

    def test_queued_message_is_sent(self):
        msg = _message("Email")
        self.assertEqual(messaging.send_message(msg.name), "Sent")
        self.assertTrue(frappe.db.get_value("Outgoing Message", msg.name, "sent_on"))

    def test_sender_must_match_channel(self):
        with self.assertRaises(frappe.ValidationError):
            _message("SMS", sender="T-mail")
