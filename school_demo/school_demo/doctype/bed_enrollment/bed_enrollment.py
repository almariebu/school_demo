# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today

from school_demo import logic


class BEdEnrollment(Document):
    def validate(self):
        self.resolve_grade()
        self.check_duplicate_active()
        self.active_key = logic.active_key(self.student, self.academic_year, self.status, self.docstatus)

    def on_cancel(self):
        self.db_set("active_key", None)

    # ------------------------------------------------------------- grade
    def resolve_grade(self):
        last = None
        if self.enrollment_type == "Continuing":
            last = get_last_enrollment(self.student, self.academic_year, exclude=self.name)
        try:
            self.grade_level = logic.resolve_grade_level(
                self.enrollment_type, self.incoming_grade_level, last.grade_level if last else None
            )
        except logic.LogicError as e:
            frappe.throw(str(e), title=_("Grade Level"))
        self.last_enrollment = last.name if last else None

    # --------------------------------------------------------- uniqueness
    def check_duplicate_active(self):
        """Friendly check first; the unique `active_key` column is the hard guarantee."""
        if self.status != "Active":
            return
        duplicate = frappe.db.exists(
            "BEd Enrollment",
            {
                "student": self.student,
                "academic_year": self.academic_year,
                "status": "Active",
                "docstatus": ["<", 2],
                "name": ["!=", self.name or ""],
            },
        )
        if duplicate:
            frappe.throw(
                _("{0} already has an active enrollment for {1} ({2}).").format(
                    self.student, self.academic_year, duplicate
                ),
                title=_("Duplicate Enrollment"),
            )


def get_last_enrollment(student, academic_year, exclude=None):
    """Most recent completed (submitted, still Active) enrollment before ``academic_year``."""
    rows = frappe.get_all(
        "BEd Enrollment",
        filters={
            "student": student,
            "docstatus": 1,
            "status": "Active",
            "academic_year": ["<", academic_year or ""],
            "name": ["!=", exclude or ""],
        },
        fields=["name", "grade_level", "academic_year"],
        order_by="academic_year desc",
        limit=1,
    )
    return rows[0] if rows else None


@frappe.whitelist()
def get_grade_level(student, academic_year, enrollment_type, incoming_grade_level=None):
    """Preview used by the form so the clerk sees the resulting grade before saving."""
    last = get_last_enrollment(student, academic_year) if enrollment_type == "Continuing" else None
    try:
        return logic.resolve_grade_level(
            enrollment_type, incoming_grade_level, last.grade_level if last else None
        )
    except logic.LogicError as e:
        frappe.throw(str(e))


@frappe.whitelist()
def withdraw(name, reason=None):
    """Withdraw a submitted enrollment and clear everything that hangs off it."""
    doc = frappe.get_doc("BEd Enrollment", name)
    doc.check_permission("write")
    if doc.docstatus != 1:
        frappe.throw(_("Only a submitted enrollment can be withdrawn."))
    if doc.status == "Withdrawn":
        frappe.throw(_("This enrollment is already withdrawn."))

    plan = logic.withdrawal_plan(doc.grade_level)
    result = {"class_lists": 0, "student_grades": 0}

    doc.db_set(
        {"status": "Withdrawn", "withdrawal_date": today(), "withdrawal_reason": reason, "active_key": None}
    )

    if plan["clear_class_list"]:
        for class_list in frappe.get_all("Class List", filters={"academic_year": doc.academic_year}, pluck="name"):
            cl = frappe.get_doc("Class List", class_list)
            kept = [r for r in cl.students if r.student != doc.student]
            if len(kept) != len(cl.students):
                cl.set("students", kept)
                cl.flags.ignore_permissions = True
                cl.save()
                result["class_lists"] += 1

    if plan["clear_student_grades"]:
        filters = {"student": doc.student, "academic_year": doc.academic_year}
        result["student_grades"] = frappe.db.count("Student Grade", filters)
        frappe.db.delete("Student Grade", filters)

    doc.add_comment(
        "Info",
        _("Withdrawn: removed from {0} class list(s), {1} grade row(s) cleared. Reason: {2}").format(
            result["class_lists"], result["student_grades"], reason or "-"
        ),
    )
    return result
