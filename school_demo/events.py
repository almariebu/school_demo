"""doc_events handlers (wired in hooks.py)."""

import frappe


def refresh_student_names(doc, method=None):
    """BEd Student on_update: keep denormalised names in Class Lists and grades current."""
    if not doc.student_name:
        return
    frappe.db.sql(
        "UPDATE `tabClass List Student` SET student_name = %s WHERE student = %s AND IFNULL(student_name, '') != %s",
        (doc.student_name, doc.name, doc.student_name),
    )
    frappe.db.sql(
        "UPDATE `tabStudent Grade` SET student_name = %s WHERE student = %s AND IFNULL(student_name, '') != %s",
        (doc.student_name, doc.name, doc.student_name),
    )


def after_student_rename(doc, method=None, old=None, new=None, merge=False):
    """BEd Student after_rename: Frappe re-points links; we re-sync the display names."""
    refresh_student_names(doc)
