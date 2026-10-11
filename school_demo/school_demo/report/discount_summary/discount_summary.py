# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

"""Script Report: every discount, filtered by school year, semester and discount type."""

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Discount"), "fieldname": "name", "fieldtype": "Link", "options": "Student Discount", "width": 120},
        {"label": _("Applicant"), "fieldname": "applicant_name", "fieldtype": "Data", "width": 180},
        {"label": _("School Year"), "fieldname": "school_year", "fieldtype": "Data", "width": 100},
        {"label": _("Semester"), "fieldname": "semester", "fieldtype": "Data", "width": 110},
        {"label": _("Type"), "fieldname": "discount_type", "fieldtype": "Data", "width": 120},
        {"label": _("Computed From"), "fieldname": "basis", "fieldtype": "Data", "width": 110},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    conditions, values = [], {}
    for field, column in [("school_year", "t.school_year"), ("semester", "t.semester"), ("discount_type", "d.discount_type")]:
        if filters.get(field):
            conditions.append(f"{column} = %({field})s")
            values[field] = filters[field]
    where = ("where " + " and ".join(conditions)) if conditions else ""
    return frappe.db.sql(
        f"""select d.name, d.applicant_name, t.school_year, t.semester, d.discount_type, d.basis, d.amount
        from `tabStudent Discount` d join `tabAcademic Term` t on t.name = d.academic_term
        {where} order by t.school_year, t.semester, d.discount_type, d.applicant_name""",
        values,
        as_dict=True,
    )
