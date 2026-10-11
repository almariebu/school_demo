"""Plain-unittest tests for school_demo.logic (no bench, no frappe needed).

Run from the repo root:  python3 -m unittest tests.test_logic -v
"""

import datetime
import unittest

from school_demo import logic
from school_demo.logic import LogicError


class UnitLimitTests(unittest.TestCase):
    def test_total_units(self):
        self.assertEqual(logic.total_units([3, 3, 2, None, ""]), 8)

    def test_within_limit(self):
        self.assertEqual(logic.check_unit_limit(24, 24), 24)

    def test_over_limit_raises(self):
        with self.assertRaises(LogicError):
            logic.check_unit_limit(24.5, 24)

    def test_zero_limit_means_unlimited(self):
        self.assertEqual(logic.check_unit_limit(99, 0), 99)


class FeeTests(unittest.TestCase):
    def test_totals(self):
        t = logic.compute_fee_totals(21, 550, [500, 300.5, 1200])
        self.assertEqual(t["tuition_total"], 11550)
        self.assertEqual(t["misc_total"], 2000.5)
        self.assertEqual(t["total_fees"], 13550.5)

    def test_empty_misc(self):
        self.assertEqual(logic.compute_fee_totals(3, 100, [])["total_fees"], 300)

    def test_downpayment_met(self):
        self.assertTrue(logic.check_downpayment(5000, 5000))
        self.assertTrue(logic.check_downpayment(7000, 5000))

    def test_downpayment_short(self):
        with self.assertRaises(LogicError):
            logic.check_downpayment(4999.99, 5000)

    def test_downpayment_none_paid(self):
        with self.assertRaises(LogicError):
            logic.check_downpayment(None, 1)

    def test_payment_status(self):
        self.assertEqual(logic.payment_status(0, 5000, 20000), "Unpaid")
        self.assertEqual(logic.payment_status(1000, 5000, 20000), "Partial")
        self.assertEqual(logic.payment_status(5000, 5000, 20000), "Down Payment Met")
        self.assertEqual(logic.payment_status(20000, 5000, 20000), "Fully Paid")


class NormalizationTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(logic.normalize_name("  MA. cristina   dela cRUZ "), "Ma. Cristina Dela Cruz")
        self.assertEqual(logic.normalize_name("juan de la cruz jr"), "Juan de la Cruz Jr.")
        self.assertEqual(logic.normalize_name("o'brien-santos"), "O'Brien-Santos")
        self.assertEqual(logic.normalize_name(None), "")

    def test_mobile(self):
        for raw in ("0917 123 4567", "+63 917 123 4567", "9171234567", "639171234567"):
            self.assertEqual(logic.normalize_mobile(raw), "+639171234567")
        self.assertEqual(logic.normalize_mobile("12345"), "")
        self.assertEqual(logic.normalize_mobile("0217123456"), "")

    def test_email(self):
        self.assertEqual(logic.normalize_email(" Juan@Example.PH "), "juan@example.ph")
        self.assertEqual(logic.normalize_email("not-an-email"), "")

    def test_payload_normalizes(self):
        p = logic.build_student_payload(
            {"first_name": "JUAN", "last_name": "dela cruz", "email": "J@X.PH", "mobile": "09171234567", "program": "BSIT"}
        )
        self.assertEqual(p["student_name"], "Juan Dela Cruz")
        self.assertEqual(p["mobile"], "+639171234567")
        self.assertEqual(p["email"], "j@x.ph")

    def test_payload_never_wipes_existing(self):
        existing = {"student_name": "Juan Dela Cruz", "mobile": "+639171234567", "email": "j@x.ph", "gender": "Male"}
        # applicant record later got corrupted / emptied
        bad = {"first_name": "", "last_name": "", "mobile": "garbage", "email": "", "gender": None}
        p = logic.build_student_payload(bad, existing)
        self.assertEqual(p, {k: existing[k] for k in existing})

    def test_payload_is_idempotent(self):
        applicant = {"first_name": "ana", "last_name": "reyes", "mobile": "09181112222"}
        first = logic.build_student_payload(applicant)
        second = logic.build_student_payload(applicant, first)
        self.assertEqual(first, second)


class ScheduleTests(unittest.TestCase):
    def test_to_minutes_variants(self):
        self.assertEqual(logic.to_minutes("07:30:00"), 450)
        self.assertEqual(logic.to_minutes("7:30"), 450)
        self.assertEqual(logic.to_minutes(datetime.timedelta(hours=7, minutes=30)), 450)
        self.assertEqual(logic.to_minutes(datetime.time(7, 30)), 450)
        with self.assertRaises(LogicError):
            logic.to_minutes("25:00")

    def test_range(self):
        self.assertEqual(logic.check_time_range("07:00", "08:30"), (420, 510))
        with self.assertRaises(LogicError):
            logic.check_time_range("09:00", "09:00")

    def test_overlap(self):
        self.assertTrue(logic.times_overlap("07:00", "08:30", "08:00", "09:00"))
        self.assertFalse(logic.times_overlap("07:00", "08:00", "08:00", "09:00"))


class GradeLevelTests(unittest.TestCase):
    def test_sequence(self):
        self.assertEqual(logic.GRADE_LEVELS[0], "Kinder")
        self.assertEqual(len(logic.GRADE_LEVELS), 13)

    def test_next_grade(self):
        self.assertEqual(logic.next_grade_level("Kinder"), "Grade 1")
        self.assertEqual(logic.next_grade_level("Grade 6"), "Grade 7")
        self.assertEqual(logic.next_grade_level("Grade 11"), "Grade 12")

    def test_grade_12_cannot_promote(self):
        with self.assertRaises(LogicError):
            logic.next_grade_level("Grade 12")

    def test_unknown_grade(self):
        with self.assertRaises(LogicError):
            logic.next_grade_level("Grade 13")

    def test_new_keeps_incoming(self):
        self.assertEqual(logic.resolve_grade_level("New", "Grade 4", None), "Grade 4")
        # a stale last grade must not influence a new student
        self.assertEqual(logic.resolve_grade_level("New", "Grade 4", "Grade 9"), "Grade 4")

    def test_new_requires_incoming(self):
        with self.assertRaises(LogicError):
            logic.resolve_grade_level("New", "", None)

    def test_continuing_moves_up(self):
        self.assertEqual(logic.resolve_grade_level("Continuing", None, "Grade 7"), "Grade 8")
        self.assertEqual(logic.resolve_grade_level("Continuing", "Grade 1", "Kinder"), "Grade 1")

    def test_continuing_needs_history(self):
        with self.assertRaises(LogicError):
            logic.resolve_grade_level("Continuing", None, None)

    def test_active_key(self):
        self.assertEqual(logic.active_key("S1", "2026-2027", "Active", 1), "S1|2026-2027")
        self.assertIsNone(logic.active_key("S1", "2026-2027", "Withdrawn", 1))
        self.assertIsNone(logic.active_key("S1", "2026-2027", "Active", 2))

    def test_withdrawal_plan(self):
        self.assertEqual(logic.withdrawal_plan("Grade 5"), {"clear_class_list": True, "clear_student_grades": False})
        self.assertTrue(logic.withdrawal_plan("Grade 11")["clear_student_grades"])
        self.assertTrue(logic.withdrawal_plan("Grade 12")["clear_student_grades"])

    def test_lrn_and_grade(self):
        self.assertEqual(logic.check_lrn("1234 5678 9012"), "123456789012")
        self.assertEqual(logic.check_lrn(""), "")
        with self.assertRaises(LogicError):
            logic.check_lrn("123")
        self.assertEqual(logic.check_grade(88.5), 88.5)
        with self.assertRaises(LogicError):
            logic.check_grade(101)


class PermissionTests(unittest.TestCase):
    def test_restricted_teacher(self):
        self.assertTrue(logic.is_teacher_restricted(["Teacher", "Desk User"]))

    def test_privileged_not_restricted(self):
        self.assertFalse(logic.is_teacher_restricted(["Teacher", "Registrar"]))
        self.assertFalse(logic.is_teacher_restricted(["Cashier"]))

    def test_access(self):
        roles = ["Teacher"]
        self.assertTrue(logic.teacher_can_access(roles, "a@x.ph", "a@x.ph"))
        self.assertFalse(logic.teacher_can_access(roles, "a@x.ph", "b@x.ph"))
        self.assertFalse(logic.teacher_can_access(roles, "a@x.ph", None))
        self.assertTrue(logic.teacher_can_access(["Registrar"], "a@x.ph", "b@x.ph"))


class ReportTests(unittest.TestCase):
    def test_pivot(self):
        states = ["Draft", "Pending Dean", "Enrolled"]
        rows = [
            {"academic_term": "T1", "workflow_state": "Draft", "cnt": 2},
            {"academic_term": "T1", "workflow_state": "Enrolled", "cnt": 3},
            {"academic_term": "T2", "workflow_state": "Pending Dean", "cnt": 1},
        ]
        out = logic.pivot_counts(rows, states)
        self.assertEqual([r["academic_term"] for r in out], ["T2", "T1"])
        t1 = out[1]
        self.assertEqual((t1["draft"], t1["pending_dean"], t1["enrolled"], t1["total"]), (2, 0, 3, 5))


if __name__ == "__main__":
    unittest.main()


class OnlinePaymentTests(unittest.TestCase):
    FEES = [
        {"id": "F2", "due": "2026-09-01", "amount": 3000, "paid": 0},
        {"id": "F1", "due": "2026-08-01", "amount": 5000, "paid": 4000},
        {"id": "F3", "due": "2026-10-01", "amount": 2000, "paid": 2000},
    ]

    def test_oldest_due_first_and_paid_fee_skipped(self):
        r = logic.allocate_payment(2500, self.FEES)
        self.assertEqual(r["applied"], {"F1": 1000, "F2": 1500})
        self.assertEqual(r["credit"], 0)

    def test_overpayment_becomes_credit(self):
        r = logic.allocate_payment(10000, self.FEES)
        self.assertEqual(r["applied"], {"F1": 1000, "F2": 3000})
        self.assertEqual(r["credit"], 6000)

    def test_zero_amount_raises(self):
        with self.assertRaises(LogicError):
            logic.allocate_payment(0, self.FEES)

    def test_payment_link_from_settings(self):
        link = logic.build_payment_link(" https://pay.example.ph/ ", "M-1", "PAY 001")
        self.assertEqual(link, "https://pay.example.ph/pay?merchant=M-1&ref=PAY%20001")

    def test_payment_link_needs_https_and_merchant(self):
        with self.assertRaises(LogicError):
            logic.build_payment_link("http://pay.example.ph", "M-1", "R")
        with self.assertRaises(LogicError):
            logic.build_payment_link("https://pay.example.ph", " ", "R")

    def test_signature_check(self):
        body = b'{"reference":"R1","amount":100}'
        sig = logic.sign_payload("s3cret", body)
        self.assertTrue(logic.verify_signature("s3cret", body, sig))
        self.assertFalse(logic.verify_signature("s3cret", body + b" ", sig))
        self.assertFalse(logic.verify_signature("", body, sig))
        self.assertFalse(logic.verify_signature("s3cret", body, None))


class MessagingTests(unittest.TestCase):
    SENDERS = [
        {"name": "old-sms", "channel": "SMS", "enabled": 0, "is_default": 0},
        {"name": "new-sms", "channel": "SMS", "enabled": 1, "is_default": 0},
        {"name": "mail-a", "channel": "Email", "enabled": 0, "is_default": 1},
        {"name": "mail-b", "channel": "Email", "enabled": 1, "is_default": 1},
    ]

    def test_preferred_sms_used_when_enabled(self):
        self.assertEqual(logic.pick_sender(self.SENDERS, "SMS", "new-sms")["name"], "new-sms")

    def test_disabled_preferred_falls_back_to_enabled(self):
        self.assertEqual(logic.pick_sender(self.SENDERS, "SMS", "old-sms")["name"], "new-sms")

    def test_no_enabled_sender_raises(self):
        with self.assertRaises(LogicError):
            logic.pick_sender([self.SENDERS[0]], "SMS", "old-sms")

    def test_default_email_account_must_be_enabled(self):
        self.assertEqual(logic.default_sender(self.SENDERS, "Email")["name"], "mail-b")
        with self.assertRaises(LogicError):
            logic.default_sender([self.SENDERS[2]], "Email")

    def test_stuck_means_missing_or_disabled_sender(self):
        self.assertTrue(logic.is_stuck("Queued", "mail-a", self.SENDERS))
        self.assertTrue(logic.is_stuck("Queued", None, self.SENDERS))
        self.assertFalse(logic.is_stuck("Queued", "mail-b", self.SENDERS))
        self.assertFalse(logic.is_stuck("Sent", "mail-a", self.SENDERS))
