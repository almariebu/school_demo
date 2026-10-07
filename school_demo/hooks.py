app_name = "school_demo"
app_title = "School Demo"
app_publisher = "Almarie Bullo"
app_description = "Live demo of two school enrollment case studies built on the Frappe Framework"
app_email = "almariebu@gmail.com"
app_license = "MIT"

# required_apps = []   # Frappe only: this app deliberately does not depend on ERPNext

# Includes in <head>
# ------------------
app_include_js = "/assets/school_demo/js/school_demo.js"

# Installation
# ------------
# Seeds demo data when the site config has "school_demo_seed": 1
after_install = "school_demo.setup.install.after_install"

# Fixtures: roles, workflow states, workflow actions and the Enrollment Assessment workflow
# -----------------------------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Dean", "Registrar", "Finance Officer", "Cashier", "Teacher"]]]},
    {
        "dt": "Workflow State",
        "filters": [["name", "in", ["Draft", "Pending Dean", "Pending Registrar", "Pending Finance", "Enrolled", "Rejected"]]],
    },
    {
        "dt": "Workflow Action Master",
        "filters": [["name", "in", ["Submit for Dean Review", "Approve", "Reject", "Enroll", "Reopen"]]],
    },
    {"dt": "Workflow", "filters": [["name", "=", "Enrollment Assessment Approval"]]},
]

# Permissions: teachers only see classes and grades assigned to them (see school_demo/permissions.py)
# ---------------------------------------------------------------------------------------------------
permission_query_conditions = {
    "Class List": "school_demo.permissions.class_list_query",
    "Student Grade": "school_demo.permissions.student_grade_query",
}

has_permission = {
    "Class List": "school_demo.permissions.class_list_has_permission",
    "Student Grade": "school_demo.permissions.student_grade_has_permission",
}

# Document events: keep student names in class lists current (see school_demo/events.py)
# --------------------------------------------------------------------------------------
doc_events = {
    "BEd Student": {
        "on_update": "school_demo.events.refresh_student_names",
        "after_rename": "school_demo.events.after_student_rename",
    }
}

# Scheduled tasks: wipe and reseed the public demo every day
# -----------------------------------------------------------
scheduler_events = {
    "daily": ["school_demo.setup.reset.reset_demo"],
}
