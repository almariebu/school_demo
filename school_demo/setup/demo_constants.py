"""Static demo content shared by the seed script and the public /demo page (no frappe imports)."""

DEMO_PASSWORD = "demo1234"

DEMO_USERS = [
    {
        "email": "dean@demo.local", "first_name": "Dean", "roles": ["Dean"],
        "label": "Dean", "case": 1,
        "try_this": "Open Enrollment Assessment, filter Pending Dean, then Approve or Reject.",
    },
    {
        "email": "registrar@demo.local", "first_name": "Registrar", "roles": ["Registrar"],
        "label": "Registrar", "case": 1,
        "try_this": "Create an Applicant, make an Enrollment Assessment, add 9+ subjects to hit the unit limit, then send it to the Dean. In Basic Education, enroll a Continuing student and press Withdraw.",
    },
    {
        "email": "finance@demo.local", "first_name": "Finance", "roles": ["Finance Officer"],
        "label": "Finance Officer", "case": 1,
        "try_this": "Open a Pending Finance assessment. Try Enroll on the one with a short down payment (it is blocked), then on the fully paid one (it locks).",
    },
    {
        "email": "cashier@demo.local", "first_name": "Cashier", "roles": ["Cashier"],
        "label": "Cashier", "case": 1,
        "try_this": "Create and submit a Student Payment for the under-paid assessment, then ask Finance to retry.",
    },
    {
        "email": "teacher@demo.local", "first_name": "Teacher", "roles": ["Teacher"],
        "label": "Teacher", "case": 2,
        "try_this": "Open Class List and Student Grade. You see only your own classes (Grade 7 - Rizal, Grade 11 - STEM A).",
    },
    {
        "email": "teacher2@demo.local", "first_name": "Teacher Two", "roles": ["Teacher"],
        "label": "Teacher (second)", "case": 2,
        "try_this": "Compare with teacher@demo.local: a different adviser sees a different set of classes.",
    },
]

CASE_STUDIES = [
    {
        "title": "Case study 1: College admission and enrollment",
        "steps": [
            "Applicant, then Enrollment Assessment (subjects and fees), then Enrolled Student.",
            "Approval chain: Draft, Pending Dean, Pending Registrar, Pending Finance, Enrolled.",
            "Finance cannot enroll until the submitted Student Payments cover the required down payment.",
            "Subjects over the term unit limit are rejected; totals are computed on the server.",
            "Run enrollment twice: the student is updated, never duplicated or wiped.",
            "Change a submitted Class Schedule time: allowed, because the time fields allow edits after submit.",
        ],
    },
    {
        "title": "Case study 2: Basic education enrollment",
        "steps": [
            "New students keep their incoming grade; Continuing students move up one grade.",
            "A second active enrollment for the same student and school year is blocked.",
            "Withdraw clears class list rows, and for Grades 11 and 12 also leftover Student Grade rows.",
            "Class Lists show the student's current name, even after the student is renamed.",
            "Teachers see only the classes assigned to them.",
        ],
    },
]
