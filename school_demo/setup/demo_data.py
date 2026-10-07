"""Idempotent demo data for the public School Demo site.

    bench --site <site> execute school_demo.setup.demo_data.seed

Safe to run repeatedly: every record is looked up by a natural key first.
"""

import frappe
from frappe.utils.password import update_password

from school_demo.setup.demo_constants import DEMO_PASSWORD, DEMO_USERS

YEAR_NOW, YEAR_PREV = "2026-2027", "2025-2026"
TERM_NOW_KEY = {"school_year": YEAR_NOW, "semester": "1st Semester"}
TERM_PREV_KEY = {"school_year": "2025-2026", "semester": "2nd Semester"}
WORKFLOW = "Enrollment Assessment Approval"

PROGRAMS = [
    ("BSIT", "BS Information Technology", "College of Computing"),
    ("BSBA", "BS Business Administration", "College of Business"),
    ("BEED", "Bachelor of Elementary Education", "College of Education"),
]

# code, title, units, lec hours, lab hours, program (None = general education)
SUBJECTS = [
    ("IT101", "Introduction to Computing", 3, 2, 3, "BSIT"),
    ("IT102", "Computer Programming 1", 3, 2, 3, "BSIT"),
    ("GE101", "Understanding the Self", 3, 3, 0, None),
    ("GE102", "Readings in Philippine History", 3, 3, 0, None),
    ("GE103", "Mathematics in the Modern World", 3, 3, 0, None),
    ("FIL101", "Kontekstwalisadong Komunikasyon sa Filipino", 3, 3, 0, None),
    ("PE101", "Physical Fitness and Wellness", 2, 2, 0, None),
    ("NSTP1", "National Service Training Program 1", 3, 3, 0, None),
    ("BA101", "Principles of Management", 3, 3, 0, "BSBA"),
    ("ED101", "The Child and Adolescent Learner", 3, 3, 0, "BEED"),
]
SUBJECTS_BY_PROGRAM = {
    "BSIT": ["IT101", "IT102", "GE101", "GE102", "GE103", "FIL101", "PE101"],
    "BSBA": ["BA101", "GE101", "GE102", "GE103", "FIL101", "PE101", "NSTP1"],
    "BEED": ["ED101", "GE101", "GE102", "GE103", "FIL101", "PE101", "NSTP1"],
}

# code, section, day, start, end, room
SCHEDULES = [
    ("IT101", "A", "Monday", "08:00:00", "09:30:00", "IT Lab 1"),
    ("IT102", "A", "Tuesday", "08:00:00", "10:00:00", "IT Lab 2"),
    ("GE101", "A", "Monday", "10:00:00", "11:30:00", "Room 201"),
    ("GE102", "A", "Wednesday", "08:00:00", "09:30:00", "Room 202"),
    ("GE103", "A", "Thursday", "13:00:00", "14:30:00", "Room 203"),
    ("FIL101", "A", "Friday", "08:00:00", "09:30:00", "Room 204"),
    ("PE101", "A", "Saturday", "08:00:00", "10:00:00", "Gymnasium"),
    ("NSTP1", "A", "Saturday", "13:00:00", "16:00:00", "Quadrangle"),
    ("BA101", "A", "Tuesday", "13:00:00", "14:30:00", "Room 205"),
    ("ED101", "A", "Thursday", "08:00:00", "09:30:00", "Room 206"),
]

MISC_FEES = [
    ("Registration", 500), ("Library", 300), ("Laboratory", 1200),
    ("Athletics", 250), ("Student Council", 150), ("ID and Handbook", 200),
]

# first, middle, last, gender, program, workflow state, payments, email
# (a few names are deliberately messy to show normalization)
APPLICANTS = [
    ("JUAN MIGUEL", "", "dela cruz", "Male", "BSIT", "Enrolled", [5000, 3000], "juan.delacruz@example.ph", "0917 123 4567"),
    ("Maria Clarissa", "Lopez", "Santos", "Female", "BSBA", "Enrolled", [6500], "maria.santos@example.ph", "09181234567"),
    ("jose antonio", "", "Reyes", "Male", "BSIT", "Enrolled", [5000], "jose.reyes@example.ph", "+63 919 555 0101"),
    ("Angelica Mae", "", "Bautista", "Female", "BEED", "Pending Finance", [5000], "angelica.bautista@example.ph", "09201112233"),
    ("Mark Joseph", "", "Villanueva", "Male", "BSIT", "Pending Finance", [1500], "mark.villanueva@example.ph", "09211112233"),
    ("Kristine Joy", "", "Mendoza", "Female", "BSBA", "Pending Registrar", [], "kristine.mendoza@example.ph", "09221112233"),
    ("Rommel", "", "Garcia", "Male", "BSIT", "Pending Registrar", [], "rommel.garcia@example.ph", "09231112233"),
    ("Patricia Anne", "", "Ramos", "Female", "BEED", "Pending Dean", [], "patricia.ramos@example.ph", "09241112233"),
    ("Christian Paul", "", "Aquino", "Male", "BSIT", "Pending Dean", [], "christian.aquino@example.ph", "09251112233"),
    ("Jasmine Rose", "", "Navarro", "Female", "BSBA", "Draft", [], "jasmine.navarro@example.ph", "09261112233"),
    ("Carlo Emmanuel", "", "Pascual", "Male", "BSIT", "Draft", [], "carlo.pascual@example.ph", "n/a"),
    ("Bernadette", "Lim", "Tan", "Female", "BSBA", "Rejected", [], "bernadette.tan@example.ph", "09271112233"),
    ("Ronaldo", "", "Castillo", "Male", "BEED", None, [], "ronaldo.castillo@example.ph", "09281112233"),
    ("Lourdes", "", "Fernandez", "Female", "BSBA", None, [], "lourdes.fernandez@example.ph", "09291112233"),
    ("Gabriel Luis", "", "Torres", "Male", "BSIT", None, [], "gabriel.torres@example.ph", "09301112233"),
]

# name, LRN, last-year grade (None = new), this-year type, incoming grade for new students
BED_STUDENTS = [
    ("Mateo Santiago Cruz", "104455660001", "Grade 6", "Continuing", None),
    ("Isabella Marie Dizon", "104455660002", "Grade 7", "Continuing", None),
    ("Rafael Antonio Lim", "104455660003", "Grade 10", "Continuing", None),
    ("Sofia Beatriz Ocampo", "104455660004", "Grade 11", "Continuing", None),
    ("Liam Joseph Padilla", "104455660005", "Kinder", "Continuing", None),
    ("Chloe Anne Mercado", "104455660006", None, "New", "Grade 1"),
    ("Nathan Gabriel Soriano", "104455660007", None, "New", "Grade 7"),
    ("Hannah Grace Alvarez", "104455660008", None, "New", "Kinder"),
    ("Elijah Matthew Cabrera", "104455660009", None, "New", "Grade 11"),
    ("Bianca Louise Tolentino", "104455660010", None, "New", "Grade 4"),
    ("Dominic Paul Aguilar", "104455660011", "Grade 2", "Continuing", None),
    ("Trisha Mae Valdez", "104455660012", None, "New", "Grade 12"),
]
# class name, grade, adviser, LRNs
CLASS_LISTS = [
    ("Grade 7 - Rizal", "Grade 7", "teacher@demo.local", ["104455660001", "104455660007"]),
    ("Grade 11 - STEM A", "Grade 11", "teacher@demo.local", ["104455660003", "104455660009"]),
    ("Grade 12 - STEM A", "Grade 12", "teacher2@demo.local", ["104455660004", "104455660012"]),
    ("Grade 1 - Mabini", "Grade 1", "teacher2@demo.local", ["104455660005", "104455660006"]),
]
SHS_AREAS = ["Oral Communication", "General Mathematics", "Earth and Life Science"]


# ------------------------------------------------------------------ helpers
def _insert(values, submit=False):
    doc = frappe.get_doc(values)
    doc.flags.ignore_permissions = True
    doc.insert()
    if submit:
        doc.submit()
    return doc


def _get_or_create(doctype, key, values=None, submit=False):
    name = frappe.db.get_value(doctype, key)
    if name:
        return frappe.get_doc(doctype, name)
    return _insert({"doctype": doctype, **key, **(values or {})}, submit=submit)


# --------------------------------------------------------------------- seed
def seed():
    """Create the full demo data set. Idempotent."""
    _prerequisites()
    _users()
    _masters()
    _college_admission()
    _basic_education()
    frappe.db.commit()
    return "School Demo data is ready."


def _prerequisites():
    for role in {r for u in DEMO_USERS for r in u["roles"]}:
        if not frappe.db.exists("Role", role):
            _insert({"doctype": "Role", "role_name": role, "desk_access": 1})
    if not frappe.db.exists("Workflow", WORKFLOW):
        from frappe.utils.fixtures import sync_fixtures

        sync_fixtures("school_demo")
    try:
        if frappe.db.exists("Currency", "PHP"):
            frappe.db.set_value("Currency", "PHP", "enabled", 1)
            if not frappe.db.get_default("currency"):
                frappe.db.set_default("currency", "PHP")
    except Exception:
        pass


def _users():
    for u in DEMO_USERS:
        if not frappe.db.exists("User", u["email"]):
            _insert(
                {
                    "doctype": "User", "email": u["email"], "first_name": u["first_name"], "last_name": "Demo",
                    "enabled": 1, "user_type": "System User", "send_welcome_email": 0,
                    "roles": [{"role": r} for r in u["roles"]],
                }
            )
        else:
            frappe.get_doc("User", u["email"]).add_roles(*u["roles"])
        update_password(u["email"], DEMO_PASSWORD)  # also restores the password after a public-demo tamper


def _masters():
    now = _get_or_create("Academic Term", TERM_NOW_KEY, {"max_units": 24, "is_active": 1})
    _get_or_create("Academic Term", TERM_PREV_KEY, {"max_units": 21, "is_active": 0})
    for code, name, dept in PROGRAMS:
        _get_or_create("Program", {"program_code": code}, {"program_name": name, "department": dept})
    for code, title, units, lec, lab, program in SUBJECTS:
        _get_or_create(
            "Course Subject", {"subject_code": code},
            {"title": title, "units": units, "lec_hours": lec, "lab_hours": lab, "program": program},
        )
    _get_or_create(
        "Fee Structure", {"academic_term": now.name},
        {"tuition_per_unit": 550, "required_downpayment": 5000,
         "misc_fees": [{"fee_name": n, "amount": a} for n, a in MISC_FEES]},
    )
    for code, section, day, start, end, room in SCHEDULES:
        key = {"academic_term": now.name, "subject": code, "section": section, "docstatus": ["<", 2]}
        if not frappe.db.exists("Class Schedule", key):
            _insert(
                {"doctype": "Class Schedule", "academic_term": now.name, "subject": code, "section": section,
                 "day": day, "start_time": start, "end_time": end, "room": room},
                submit=True,
            )


# ----------------------------------------------------------------- case 1
def _college_admission():
    term = frappe.db.get_value("Academic Term", TERM_NOW_KEY)
    for first, middle, last, gender, program, state, payments, email, mobile in APPLICANTS:
        applicant = frappe.db.get_value("Applicant", {"email": email})
        if not applicant:
            applicant = _insert(
                {
                    "doctype": "Applicant", "first_name": first, "middle_name": middle, "last_name": last,
                    "gender": gender, "program": program, "academic_term": term, "email": email, "mobile": mobile,
                    "previous_school": "Sample National High School",
                }
            ).name
        if state is None:
            continue
        _assessment(applicant, term, program, state, payments)


def _assessment(applicant, term, program, state, payments):
    if frappe.db.exists("Enrollment Assessment", {"applicant": applicant, "academic_term": term, "docstatus": ["<", 2]}):
        return
    doc = _insert(
        {
            "doctype": "Enrollment Assessment", "applicant": applicant, "academic_term": term, "program": program,
            "subjects": [{"subject": s} for s in SUBJECTS_BY_PROGRAM[program]],
        }
    )
    for amount in payments:
        _insert(
            {"doctype": "Student Payment", "assessment": doc.name, "amount": amount,
             "payment_type": "Down Payment", "mode_of_payment": "GCash"},
            submit=True,
        )
    doc = frappe.get_doc("Enrollment Assessment", doc.name)
    doc.flags.ignore_permissions = True
    doc.save()  # refresh amount_paid / payment_status

    if state == "Enrolled":
        _force_enroll(doc)
    elif state != "Draft":
        frappe.db.set_value("Enrollment Assessment", doc.name, "workflow_state", state, update_modified=False)
    applicant_status = {"Enrolled": "Enrolled", "Rejected": "Rejected"}.get(state, "Under Assessment")
    if state == "Enrolled":
        applicant_status = None  # on_submit already set it
    if applicant_status:
        frappe.db.set_value("Applicant", applicant, "status", applicant_status, update_modified=False)


def _force_enroll(doc):
    """Lock an assessment as Enrolled the way the Finance transition would.

    The payment gate still runs; only the interactive workflow engine is bypassed
    so the seed does not depend on the seeding user's workflow permissions.
    """
    doc.check_payment()
    doc.docstatus = 1
    doc.workflow_state = "Enrolled"
    frappe.db.set_value(
        "Enrollment Assessment", doc.name,
        {"docstatus": 1, "workflow_state": "Enrolled", "amount_paid": doc.amount_paid, "payment_status": doc.payment_status},
        update_modified=False,
    )
    for child in ("Assessment Subject", "Assessment Fee"):
        frappe.db.sql(f"UPDATE `tab{child}` SET docstatus = 1 WHERE parent = %s", doc.name)
    doc.run_method("on_submit")


# ----------------------------------------------------------------- case 2
def _basic_education():
    students = {}
    for name, lrn, prev_grade, kind, incoming in BED_STUDENTS:
        students[lrn] = _get_or_create("BEd Student", {"lrn": lrn}, {"student_name": name}).name
        if prev_grade:
            _bed_enrollment(students[lrn], YEAR_PREV, "New", prev_grade)
        _bed_enrollment(students[lrn], YEAR_NOW, kind, incoming)

    for class_name, grade, adviser, lrns in CLASS_LISTS:
        class_list = _get_or_create(
            "Class List", {"class_name": class_name, "academic_year": YEAR_NOW},
            {"grade_level": grade, "adviser": adviser, "students": [{"student": students[l]} for l in lrns]},
        )
        if grade in ("Grade 11", "Grade 12"):
            for row in class_list.students:
                for area in SHS_AREAS:
                    _get_or_create(
                        "Student Grade",
                        {"student": row.student, "class_list": class_list.name, "learning_area": area, "quarter": "Q1"},
                        {"grade": 84 + (len(row.student) + len(area)) % 12},
                    )


def _bed_enrollment(student, year, kind, incoming):
    if frappe.db.exists("BEd Enrollment", {"student": student, "academic_year": year, "docstatus": ["<", 2]}):
        return
    _insert(
        {"doctype": "BEd Enrollment", "student": student, "academic_year": year,
         "enrollment_type": kind, "incoming_grade_level": incoming},
        submit=True,
    )
