# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

"""Script Report: quarterly grades per learning area with the final grade and remarks.

Reads through ``frappe.get_list`` so a teacher only sees the grades they own, and the
student name always comes from the BEd Student record (not a stale copy).
"""

import frappe
from frappe import _

from school_demo import logic


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = {k: filters[k] for k in ("academic_year", "class_list") if filters.get(k)}
    rows = frappe.get_list(
        "Student Grade",
        filters=conditions,
        fields=["student", "learning_area", "quarter", "grade", "grade_level"],
        limit_page_length=0,
    )
    names = dict(frappe.get_all("BEd Student", fields=["name", "student_name"], as_list=True))
    grouped = {}
    for r in rows:
        entry = grouped.setdefault(
            (r.student, r.learning_area), {"student": r.student, "learning_area": r.learning_area, "grade_level": r.grade_level, "grades": {}}
        )
        entry["grades"][r.quarter] = r.grade
    data = []
    for (student, _area), entry in sorted(grouped.items(), key=lambda kv: (names.get(kv[0][0], ""), kv[0][1])):
        final = logic.final_grade(entry["grades"])
        data.append(
            {"student": student, "student_name": names.get(student, student), "grade_level": entry["grade_level"],
             "learning_area": entry["learning_area"], **{q: entry["grades"].get(q) for q in logic.QUARTERS},
             "average": final["average"], "remarks": final["remarks"]}
        )
    return get_columns(), data


def get_columns():
    columns = [
        {"label": _("Student"), "fieldname": "student_name", "fieldtype": "Data", "width": 180},
        {"label": _("Grade Level"), "fieldname": "grade_level", "fieldtype": "Data", "width": 100},
        {"label": _("Learning Area"), "fieldname": "learning_area", "fieldtype": "Data", "width": 160},
    ]
    columns += [{"label": q, "fieldname": q, "fieldtype": "Float", "precision": 0, "width": 60} for q in logic.QUARTERS]
    columns += [
        {"label": _("Final Grade"), "fieldname": "average", "fieldtype": "Float", "precision": 2, "width": 100},
        {"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 100},
    ]
    return columns
