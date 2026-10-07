"""Case 1: turning an approved Enrollment Assessment into an Enrolled Student.

The operation is idempotent: it is a get-or-update keyed on (applicant, academic
term). Running it again never creates a second student and never blanks data
that the student already has (see ``logic.build_student_payload``).
"""

import frappe
from frappe.utils import today

from school_demo import logic


def _applicant_data(assessment) -> dict:
    """Copy of the applicant record. A missing/broken applicant must not break enrollment."""
    try:
        data = frappe.get_doc("Applicant", assessment.applicant).as_dict()
    except Exception:
        frappe.log_error(title="School Demo: applicant unreadable during enrollment")
        data = frappe._dict(full_name=assessment.get("applicant_name"))
    data = dict(data)
    if assessment.get("program"):
        data["program"] = assessment.program
    data["academic_term"] = assessment.academic_term
    return data


def enroll_from_assessment(assessment) -> str:
    """Get-or-update the Enrolled Student for this assessment. Returns its name."""
    existing_name = frappe.db.get_value(
        "Enrolled Student", {"applicant": assessment.applicant, "academic_term": assessment.academic_term}
    )
    if existing_name:
        student = frappe.get_doc("Enrolled Student", existing_name)
        existing = student.as_dict()
    else:
        student = frappe.new_doc("Enrolled Student")
        existing = {}

    payload = logic.build_student_payload(_applicant_data(assessment), existing)
    payload.setdefault("student_name", assessment.get("applicant_name") or assessment.applicant)
    student.update(payload)
    student.update(
        {
            "applicant": assessment.applicant,
            "academic_term": assessment.academic_term,
            "assessment": assessment.name,
            "total_units": assessment.total_units,
            "status": "Enrolled",
        }
    )
    if not student.get("enrolled_on"):
        student.enrolled_on = today()
    student.flags.ignore_permissions = True
    student.save()

    if frappe.db.exists("Applicant", assessment.applicant):
        frappe.db.set_value(
            "Applicant", assessment.applicant, {"status": "Enrolled", "student": student.name}, update_modified=False
        )
    return student.name


def release_student(assessment) -> None:
    """Assessment cancelled: mark the student record instead of deleting history."""
    name = frappe.db.get_value(
        "Enrolled Student",
        {"applicant": assessment.applicant, "academic_term": assessment.academic_term, "assessment": assessment.name},
    )
    if name:
        frappe.db.set_value("Enrolled Student", name, "status", "Cancelled")
    if frappe.db.exists("Applicant", assessment.applicant):
        frappe.db.set_value("Applicant", assessment.applicant, "status", "Under Assessment", update_modified=False)
