# Copyright (c) 2026, Almarie Bullo and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from school_demo import logic


class ClassSchedule(Document):
    def validate(self):
        self.check_schedule()

    def before_update_after_submit(self):
        """Staff may still change day/time/room/instructor after submit (allow_on_submit)."""
        self.check_schedule()

    def check_schedule(self):
        try:
            logic.check_time_range(self.start_time, self.end_time)
        except logic.LogicError as e:
            frappe.throw(str(e))
        others = frappe.get_all(
            "Class Schedule",
            filters={
                "academic_term": self.academic_term,
                "day": self.day,
                "docstatus": ["<", 2],
                "name": ["!=", self.name or ""],
            },
            fields=["name", "room", "instructor", "start_time", "end_time"],
        )
        for other in others:
            if not logic.times_overlap(self.start_time, self.end_time, other.start_time, other.end_time):
                continue
            if self.room and other.room == self.room:
                frappe.throw(_("Room {0} is already booked by {1} at that time.").format(self.room, other.name))
            if self.instructor and other.instructor == self.instructor:
                frappe.throw(_("{0} already teaches {1} at that time.").format(self.instructor, other.name))
