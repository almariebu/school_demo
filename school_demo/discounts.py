"""Batch discounts: one rule applied to many assessments."""

import json

import frappe
from frappe import _

from school_demo import logic


@frappe.whitelist()
def apply_discount_batch(rule, assessments):
    """Create a Student Discount per assessment. One that already has this type is skipped."""
    rule = frappe._dict(json.loads(rule) if isinstance(rule, str) else rule)
    assessments = json.loads(assessments) if isinstance(assessments, str) else assessments
    if not assessments:
        frappe.throw(_("Select at least one student."))
    added, skipped = [], []
    for assessment in assessments:
        if frappe.db.exists("Student Discount", {"assessment": assessment, "discount_type": rule.discount_type}):
            skipped.append(assessment)
            continue
        frappe.get_doc(
            {"doctype": "Student Discount", "assessment": assessment, "discount_type": rule.discount_type,
             "basis": rule.basis, "mode": rule.mode, "value": rule.value}
        ).insert()  # permissions apply: Finance Officer only
        added.append(assessment)
    return {"added": added, "skipped": skipped}
