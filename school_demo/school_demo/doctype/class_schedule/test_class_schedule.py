# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo.tests import utils


def make_schedule(term, subject, section, day="Monday", start="08:00:00", end="09:30:00", room="R-101", submit=True):
    doc = frappe.get_doc({
        "doctype": "Class Schedule", "academic_term": term, "subject": subject, "section": section,
        "day": day, "start_time": start, "end_time": end, "room": room,
    })
    doc.insert()
    if submit:
        doc.submit()
    return doc


class TestClassSchedule(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.term = utils.make_term().name
        utils.make_subject("TST-S1", 3)
        utils.make_subject("TST-S2", 3)

    def test_end_must_be_after_start(self):
        with self.assertRaises(frappe.ValidationError):
            make_schedule(self.term, "TST-S1", "A", start="10:00:00", end="09:00:00", submit=False)

    def test_room_conflict_blocked(self):
        make_schedule(self.term, "TST-S1", "A")
        with self.assertRaises(frappe.ValidationError):
            make_schedule(self.term, "TST-S2", "A", start="09:00:00", end="10:00:00", submit=False)

    def test_time_can_change_after_submit(self):
        doc = make_schedule(self.term, "TST-S1", "B", day="Tuesday")
        self.assertEqual(doc.docstatus, 1)
        doc.start_time = "13:00:00"
        doc.end_time = "14:30:00"
        doc.room = "R-202"
        doc.save()  # allow_on_submit fields -> update after submit
        doc.reload()
        self.assertEqual(doc.docstatus, 1)
        self.assertEqual(doc.room, "R-202")

    def test_change_after_submit_still_checks_conflicts(self):
        make_schedule(self.term, "TST-S1", "C", day="Wednesday", room="R-303")
        other = make_schedule(self.term, "TST-S2", "C", day="Wednesday", start="11:00:00", end="12:00:00", room="R-304")
        other.room = "R-303"
        other.start_time = "08:30:00"
        other.end_time = "09:00:00"
        with self.assertRaises(frappe.ValidationError):
            other.save()
