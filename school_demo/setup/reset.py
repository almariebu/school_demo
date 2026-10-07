"""Daily clean-up for a public demo site (scheduler_events -> daily)."""

import frappe

from school_demo.setup.demo_data import seed

# children before parents
DEMO_DOCTYPES = [
    "Student Grade",
    "Class List",
    "BEd Enrollment",
    "BEd Student",
    "Student Payment",
    "Enrollment Assessment",
    "Enrolled Student",
    "Applicant",
    "Class Schedule",
    "Fee Structure",
    "Course Subject",
    "Program",
    "Academic Term",
]


def wipe_demo_docs():
    """Delete all demo records directly (bypasses link checks on purpose)."""
    for doctype in DEMO_DOCTYPES:
        meta = frappe.get_meta(doctype)
        for table_field in meta.get_table_fields():
            frappe.db.delete(table_field.options, {"parenttype": doctype})
        frappe.db.delete(doctype)
        frappe.db.delete("Version", {"ref_doctype": doctype})
        frappe.db.delete("Comment", {"reference_doctype": doctype})
        frappe.db.delete("DocShare", {"share_doctype": doctype})
        frappe.db.delete("ToDo", {"reference_type": doctype})


def reset_demo(force=False):
    """Wipe and reseed the demo. Only runs on sites that opted in with `school_demo_seed`."""
    if not force and not frappe.conf.get("school_demo_seed"):
        return
    try:
        wipe_demo_docs()
        seed()
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title="School Demo: daily reset failed")
        raise
