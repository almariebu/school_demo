# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic
from school_demo.enrollment import enroll_from_assessment, release_student


class EnrollmentAssessment(Document):
    def validate(self):
        if not self.workflow_state:
            self.workflow_state = "Draft"
        if self.docstatus == 0:
            self.pull_term_rules()
            self.pull_subject_details()
            self.calculate_units()
            self.pull_fees()
        self.set_payment_info()
        # Finance cannot move the workflow to Enrolled until the payment check passes.
        if self.workflow_state == "Enrolled":
            self.check_payment()

    def before_submit(self):
        self.check_payment()

    def on_submit(self):
        enroll_from_assessment(self)

    def on_cancel(self):
        release_student(self)

    # --------------------------------------------------------------- pulls
    def pull_term_rules(self):
        term = frappe.db.get_value("Academic Term", self.academic_term, ["max_units", "is_active"], as_dict=True)
        if not term:
            frappe.throw(_("Academic Term {0} not found.").format(self.academic_term))
        if self.is_new() and not term.is_active:
            frappe.throw(_("Academic Term {0} is not active.").format(self.academic_term))
        self.max_units = term.max_units
        fee_structure = frappe.db.get_value("Fee Structure", {"academic_term": self.academic_term})
        if not fee_structure:
            frappe.throw(_("No Fee Structure exists for {0}.").format(self.academic_term))
        self.fee_structure = fee_structure

    def pull_subject_details(self):
        seen = set()
        for row in self.subjects:
            if row.subject in seen:
                frappe.throw(_("Row {0}: {1} is listed twice.").format(row.idx, row.subject))
            seen.add(row.subject)
            # never trust client-sent units
            row.units = frappe.db.get_value("Course Subject", row.subject, "units")
        if self.workflow_state != "Draft" and not self.subjects:
            frappe.throw(_("Add at least one subject before sending this assessment for approval."))

    def calculate_units(self):
        self.total_units = logic.total_units(r.units for r in self.subjects)
        try:
            logic.check_unit_limit(self.total_units, self.max_units)
        except logic.LogicError as e:
            frappe.throw(str(e), title=_("Unit Limit Exceeded"))

    def pull_fees(self):
        fs = frappe.get_cached_doc("Fee Structure", self.fee_structure)
        totals = logic.compute_fee_totals(self.total_units, fs.tuition_per_unit, [r.amount for r in fs.misc_fees])
        self.set("fees", [])
        self.append(
            "fees",
            {
                "fee_type": "Tuition",
                "description": f"Tuition ({self.total_units:g} units x {logic.flt(fs.tuition_per_unit):,.2f})",
                "amount": totals["tuition_total"],
            },
        )
        for misc in fs.misc_fees:
            self.append("fees", {"fee_type": "Miscellaneous", "description": misc.fee_name, "amount": misc.amount})
        self.tuition_total = totals["tuition_total"]
        self.misc_total = totals["misc_total"]
        self.total_fees = totals["total_fees"]
        self.required_downpayment = fs.required_downpayment

    # ------------------------------------------------------------- payment
    def get_paid_amount(self) -> float:
        paid = frappe.db.sql(
            "SELECT COALESCE(SUM(amount), 0) FROM `tabStudent Payment` WHERE assessment = %s AND docstatus = 1",
            self.name,
        )[0][0]
        return logic.flt(paid, 2)

    def set_payment_info(self):
        self.amount_paid = self.get_paid_amount()
        self.payment_status = logic.payment_status(self.amount_paid, self.required_downpayment, self.total_fees)

    def check_payment(self):
        """Payment gate used by validate (Enrolled state) and before_submit."""
        self.set_payment_info()
        try:
            logic.check_downpayment(self.amount_paid, self.required_downpayment)
        except logic.LogicError as e:
            frappe.throw(str(e), title=_("Payment Check Failed"))
