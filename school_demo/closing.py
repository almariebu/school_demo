"""Account closing: build one ledger per locked assessment in a background job.

Unposted (draft) Student Payments block the closing. Overpayments stay on the
ledger as credit. A penalty applies from the due date itself.
"""

import frappe
from frappe import _

from school_demo import logic


def _unposted(term):
    return frappe.db.sql(
        "select count(*) from `tabStudent Payment` p join `tabEnrollment Assessment` a on a.name = p.assessment "
        "where p.docstatus = 0 and a.academic_term = %s",
        term,
    )[0][0]


@frappe.whitelist()
def start_closing(name):
    doc = frappe.get_doc("Account Closing", name)
    doc.check_permission("write")
    if doc.status in ("Queued", "Running"):
        frappe.throw(_("This closing is already {0}.").format(doc.status.lower()))
    blocker = logic.closing_blocker(doc.academic_term, frappe.db.get_value("Academic Term", doc.academic_term, "is_closed"), _unposted(doc.academic_term))
    if blocker:
        frappe.throw(blocker)
    doc.db_set({"status": "Queued", "ledgers_built": 0, "error": None})
    frappe.enqueue("school_demo.closing.run_closing", queue="long", name=name, now=bool(frappe.flags.in_test))
    return "Queued"


def run_closing(name):
    doc = frappe.get_doc("Account Closing", name)
    try:
        assessments = frappe.get_all(
            "Enrollment Assessment",
            filters={"academic_term": doc.academic_term, "docstatus": 1},
            fields=["name", "total_fees"],
        )
        doc.db_set({"status": "Running", "total": len(assessments)})
        frappe.db.delete("Student Ledger", {"closing": name})
        for index, a in enumerate(assessments, start=1):
            payments = frappe.get_all(
                "Student Payment", filters={"assessment": a.name, "docstatus": 1}, fields=["amount", "payment_type as kind"]
            )
            ledger = logic.build_ledger(a.total_fees, payments)
            ledger["penalty"] = logic.penalty_for(ledger["balance"], doc.due_date, doc.as_of_date)
            frappe.get_doc({"doctype": "Student Ledger", "closing": name, "assessment": a.name, **ledger}).insert(ignore_permissions=True)
            doc.db_set("ledgers_built", index)
        frappe.db.set_value("Academic Term", doc.academic_term, "is_closed", 1)
        doc.db_set("status", "Done")
    except Exception:
        frappe.db.rollback()
        doc.db_set({"status": "Failed", "error": frappe.get_traceback()[-500:]})
        frappe.log_error(title=f"School Demo: account closing {name} failed")
        raise
