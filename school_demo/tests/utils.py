"""Factories shared by the FrappeTestCase tests (need a bench; not used by tests/test_logic.py)."""

import frappe

TEST_YEAR = "2099-2100"
TEST_TERM = f"{TEST_YEAR} 1st Semester"


def _insert(values, submit=False):
    doc = frappe.get_doc(values)
    doc.flags.ignore_permissions = True
    doc.insert()
    if submit:
        doc.submit()
    return doc


def make_term(max_units=21, semester="1st Semester", school_year=TEST_YEAR):
    name = frappe.db.get_value("Academic Term", {"school_year": school_year, "semester": semester})
    if name:
        frappe.db.set_value("Academic Term", name, {"max_units": max_units, "is_active": 1})
        return frappe.get_doc("Academic Term", name)
    return _insert({"doctype": "Academic Term", "school_year": school_year, "semester": semester,
                    "max_units": max_units, "is_active": 1})


def make_program(code="TST-IT"):
    if frappe.db.exists("Program", code):
        return frappe.get_doc("Program", code)
    return _insert({"doctype": "Program", "program_code": code, "program_name": "Test Program"})


def make_subject(code, units=3):
    if frappe.db.exists("Course Subject", code):
        return frappe.get_doc("Course Subject", code)
    return _insert({"doctype": "Course Subject", "subject_code": code, "title": f"Subject {code}", "units": units})


def make_fee_structure(term, tuition_per_unit=500, downpayment=5000, misc=(("Registration", 300), ("Library", 200))):
    name = frappe.db.get_value("Fee Structure", {"academic_term": term})
    if name:
        frappe.delete_doc("Fee Structure", name, force=True, ignore_permissions=True)
    return _insert({
        "doctype": "Fee Structure", "academic_term": term, "tuition_per_unit": tuition_per_unit,
        "required_downpayment": downpayment,
        "misc_fees": [{"fee_name": n, "amount": a} for n, a in misc],
    })


def make_applicant(first="Juan", last="Dela Cruz", email="juan.test@example.ph", program="TST-IT", term=TEST_TERM, **kw):
    name = frappe.db.get_value("Applicant", {"email": email})
    if name:
        return frappe.get_doc("Applicant", name)
    return _insert({"doctype": "Applicant", "first_name": first, "last_name": last, "email": email,
                    "program": program, "academic_term": term, **kw})


def make_assessment(applicant, term, subjects):
    return _insert({
        "doctype": "Enrollment Assessment", "applicant": applicant, "academic_term": term,
        "subjects": [{"subject": s} for s in subjects],
    })


def make_payment(assessment, amount, submit=True):
    return _insert({"doctype": "Student Payment", "assessment": assessment, "amount": amount,
                    "payment_type": "Down Payment"}, submit=submit)


def make_bed_student(name="Test Learner", lrn=None):
    existing = frappe.db.get_value("BEd Student", {"student_name": name})
    if existing:
        return frappe.get_doc("BEd Student", existing)
    return _insert({"doctype": "BEd Student", "student_name": name, "lrn": lrn})


def make_bed_enrollment(student, academic_year, enrollment_type="New", incoming="Grade 7", submit=True):
    return _insert({"doctype": "BEd Enrollment", "student": student, "academic_year": academic_year,
                    "enrollment_type": enrollment_type, "incoming_grade_level": incoming}, submit=submit)


def make_user(email, roles):
    if not frappe.db.exists("User", email):
        frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0],
                        "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
    user = frappe.get_doc("User", email)
    user.add_roles(*roles)
    return user
