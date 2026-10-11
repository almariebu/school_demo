"""Online payment integration: payment links and the gateway webhook.

The gateway posts JSON ``{"reference", "student", "amount"}`` with an
``X-Signature`` header (HMAC-SHA256 of the raw body, keyed by the webhook secret
in School Settings). Delivery is idempotent: a repeated reference changes nothing.
"""

import json

import frappe
from frappe import _

from school_demo import logic

FINANCE_ROLES = ("Finance Officer", "System Manager")


def _throw_logic(error):
    frappe.throw(str(error))


@frappe.whitelist()
def payment_link(fee):
    frappe.has_permission("Student Fee", "read", fee, throw=True)
    settings = frappe.get_single("School Settings")
    try:
        return logic.build_payment_link(settings.payment_base_url, settings.merchant_id, fee)
    except logic.LogicError as e:
        _throw_logic(e)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def payment_webhook():
    return process_webhook(frappe.request.get_data(), frappe.get_request_header("X-Signature"))


def process_webhook(body: bytes, signature):
    secret = frappe.get_single("School Settings").get_password("webhook_secret", raise_exception=False)
    if not logic.verify_signature(secret, body, signature):
        frappe.throw(_("Invalid signature."), frappe.AuthenticationError)
    try:
        payload = json.loads(body)
    except ValueError:
        frappe.throw(_("Body must be JSON."))
    return apply_payment(payload)


def apply_payment(payload):
    reference = str(payload.get("reference") or "").strip()
    student = payload.get("student")
    if not reference or not frappe.db.exists("Enrolled Student", student):
        frappe.throw(_("Unknown reference or student."))
    amount = logic.flt(payload.get("amount"), 2)
    if amount <= 0:
        frappe.throw(_("Payment amount must be greater than zero."))
    # The reference is the document name, so the unique key makes a repeat delivery a no-op
    # even when two deliveries arrive at the same moment.
    try:
        payment = frappe.get_doc(
            {"doctype": "Online Payment", "reference": reference, "student": student, "amount": amount}
        ).insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        frappe.clear_messages()
        return {"status": "duplicate", "reference": reference}

    # Lock the open fees so two payments for one student cannot both spend the same balance.
    fees = frappe.db.sql(
        "select name as id, due_date as due, amount, paid_amount as paid from `tabStudent Fee` "
        "where student = %s and balance > 0 for update",
        student,
        as_dict=True,
    )
    result = logic.allocate_payment(amount, fees)
    for fee_id, applied in result["applied"].items():
        fee = frappe.get_doc("Student Fee", fee_id)
        fee.paid_amount = logic.flt(fee.paid_amount) + applied
        fee.save(ignore_permissions=True)
    payment.db_set(
        {
            "credit": result["credit"],
            "applied_to": "\n".join(f"{fee}: {amt:,.2f}" for fee, amt in result["applied"].items()),
        }
    )
    return {"status": "applied", **result}


@frappe.whitelist()
def simulate_payment(student, amount):
    """Stand-in for the real gateway: signs a payload and sends it through the same webhook path."""
    frappe.only_for(FINANCE_ROLES)
    secret = frappe.get_single("School Settings").get_password("webhook_secret", raise_exception=False)
    if not secret:
        frappe.throw(_("Set the gateway webhook secret in School Settings first."))
    body = json.dumps(
        {"reference": f"SIM-{frappe.generate_hash(length=8).upper()}", "student": student, "amount": amount}
    ).encode()
    return process_webhook(body, logic.sign_payload(secret, body))
