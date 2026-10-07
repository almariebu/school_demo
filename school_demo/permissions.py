"""Row-level access for teachers (hooked in hooks.py).

A user whose only school role is "Teacher" sees just the Class Lists where they
are the adviser and just the Student Grades they own. Registrar, Dean and
System Manager are not restricted.
"""

import frappe

from school_demo import logic


def _restricted(user: str) -> bool:
    if user == "Administrator":
        return False
    return logic.is_teacher_restricted(frappe.get_roles(user))


def class_list_query(user=None):
    """permission_query_conditions for Class List."""
    user = user or frappe.session.user
    if not _restricted(user):
        return ""
    return f"`tabClass List`.`adviser` = {frappe.db.escape(user)}"


def student_grade_query(user=None):
    """permission_query_conditions for Student Grade."""
    user = user or frappe.session.user
    if not _restricted(user):
        return ""
    return f"`tabStudent Grade`.`teacher` = {frappe.db.escape(user)}"


def class_list_has_permission(doc, ptype=None, user=None):
    """has_permission for Class List. Returns False to deny, None to defer to role rules."""
    user = user or frappe.session.user
    if _restricted(user) and not logic.teacher_can_access(frappe.get_roles(user), user, doc.get("adviser")):
        return False
    return None


def student_grade_has_permission(doc, ptype=None, user=None):
    """has_permission for Student Grade."""
    user = user or frappe.session.user
    if _restricted(user) and not logic.teacher_can_access(frappe.get_roles(user), user, doc.get("teacher")):
        return False
    return None
