# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

"""Script Report: number of Enrollment Assessments per workflow state, per academic term."""

import frappe
from frappe import _

from school_demo import logic

WORKFLOW = "Enrollment Assessment Approval"
DEFAULT_STATES = ["Draft", "Pending Dean", "Pending Registrar", "Pending Finance", "Enrolled", "Rejected"]


def execute(filters=None):
    filters = frappe._dict(filters or {})
    states = get_states()
    data = logic.pivot_counts(get_counts(filters), states)
    return get_columns(states), data, None, get_chart(states, data), get_summary(states, data)


def get_states():
    states = frappe.get_all("Workflow Document State", filters={"parent": WORKFLOW}, pluck="state", order_by="idx")
    return states or DEFAULT_STATES


def get_counts(filters):
    conditions = {"docstatus": ["<", 2]}
    if filters.get("academic_term"):
        conditions["academic_term"] = filters.academic_term
    return frappe.get_all(
        "Enrollment Assessment",
        filters=conditions,
        fields=["academic_term", "workflow_state", "count(name) as cnt"],
        group_by="academic_term, workflow_state",
    )


def get_columns(states):
    columns = [{"label": _("Academic Term"), "fieldname": "academic_term", "fieldtype": "Link", "options": "Academic Term", "width": 220}]
    columns += [{"label": _(s), "fieldname": logic.state_fieldname(s), "fieldtype": "Int", "width": 130} for s in states]
    columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 90})
    return columns


def get_chart(states, data):
    if not data:
        return None
    return {
        "data": {
            "labels": [row["academic_term"] for row in data],
            "datasets": [{"name": s, "values": [row.get(logic.state_fieldname(s), 0) for row in data]} for s in states],
        },
        "type": "bar",
        "barOptions": {"stacked": 1},
    }


def get_summary(states, data):
    return [
        {"value": sum(row.get(logic.state_fieldname(s), 0) for row in data), "label": _(s), "datatype": "Int"}
        for s in states
    ]
