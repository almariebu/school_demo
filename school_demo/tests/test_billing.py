import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo import closing, discounts, logic
from school_demo.school_demo.report.discount_summary import discount_summary
from school_demo.school_demo.report.student_grade_report import student_grade_report


def _submitted_assessments():
    rows = frappe.get_all("Enrollment Assessment", {"docstatus": 1}, ["name", "academic_term", "total_fees"], order_by="creation")
    assert len(rows) >= 2, "run the demo seed first: bench execute school_demo.setup.demo_data.seed"
    return rows


class TestAccountClosing(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.assessments = _submitted_assessments()
        cls.term = cls.assessments[0].academic_term

    def setUp(self):
        frappe.db.set_value("Academic Term", self.term, "is_closed", 0)
        frappe.db.delete("Student Ledger")
        frappe.db.delete("Account Closing")

    def _closing(self, due="2026-10-15", as_of="2026-10-20"):
        return frappe.get_doc({"doctype": "Account Closing", "academic_term": self.term, "due_date": due, "as_of_date": as_of}).insert()

    def test_unposted_payment_blocks_closing(self):
        draft = frappe.get_doc({"doctype": "Student Payment", "assessment": self.assessments[0].name, "amount": 100,
                                "payment_type": "Down Payment"}).insert()
        with self.assertRaises(frappe.ValidationError) as ctx:
            closing.start_closing(self._closing().name)
        self.assertIn("unposted payment", str(ctx.exception))
        frappe.delete_doc("Student Payment", draft.name, force=True)

    def test_closing_builds_a_ledger_per_assessment_and_closes_the_term(self):
        c = self._closing()
        closing.start_closing(c.name)
        c.reload()
        in_term = [a for a in self.assessments if a.academic_term == self.term]
        self.assertEqual((c.status, c.ledgers_built, c.total), ("Done", len(in_term), len(in_term)))
        self.assertEqual(frappe.db.count("Student Ledger", {"closing": c.name}), len(in_term))
        self.assertEqual(frappe.db.get_value("Academic Term", self.term, "is_closed"), 1)
        first = frappe.get_doc("Student Ledger", {"closing": c.name, "assessment": in_term[0].name})
        paid = frappe.db.sql("select coalesce(sum(amount),0) from `tabStudent Payment` where assessment=%s and docstatus=1", in_term[0].name)[0][0]
        expected = logic.build_ledger(in_term[0].total_fees, [{"amount": paid, "kind": ""}])
        self.assertEqual((first.balance, first.credit), (expected["balance"], expected["credit"]))
        self.assertEqual(first.penalty, logic.penalty_for(first.balance, "2026-10-15", "2026-10-20"))

    def test_a_closed_term_cannot_be_closed_again(self):
        c = self._closing()
        closing.start_closing(c.name)
        with self.assertRaises(frappe.ValidationError) as ctx:
            closing.start_closing(self._closing().name)
        self.assertIn("already closed", str(ctx.exception))


class TestCashCount(FrappeTestCase):
    def test_variance_against_posted_payments(self):
        a = _submitted_assessments()[0]
        frappe.db.delete("Student Payment", {"posting_date": "2031-01-02", "received_by": "Administrator"})
        frappe.get_doc({"doctype": "Student Payment", "assessment": a.name, "amount": 700, "payment_type": "Down Payment",
                        "posting_date": "2031-01-02", "received_by": "Administrator"}).insert().submit()
        cc = frappe.get_doc({"doctype": "Cash Count", "count_date": "2031-01-02", "cashier": "Administrator", "counted": 650}).insert()
        self.assertEqual((cc.expected, cc.variance, cc.status), (700, -50, "Short"))


class TestDiscounts(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.a1, cls.a2 = [a.name for a in _submitted_assessments()[:2]]

    def setUp(self):
        frappe.db.delete("Student Discount")

    def test_batch_adds_then_skips_duplicates(self):
        rule = {"discount_type": "Test Scholar", "basis": "assessment", "mode": "percent", "value": 10}
        first = discounts.apply_discount_batch(rule, [self.a1, self.a2])
        self.assertEqual((len(first["added"]), len(first["skipped"])), (2, 0))
        again = discounts.apply_discount_batch(rule, [self.a1])
        self.assertEqual((len(again["added"]), again["skipped"]), (0, [self.a1]))
        total = frappe.db.get_value("Enrollment Assessment", self.a1, "total_fees")
        self.assertEqual(frappe.db.get_value("Student Discount", {"assessment": self.a1}, "amount"), round(total * 0.1, 2))

    def test_empty_selection_and_bad_rule_are_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            discounts.apply_discount_batch({"discount_type": "X", "basis": "assessment", "mode": "percent", "value": 5}, [])
        with self.assertRaises(frappe.ValidationError):
            discounts.apply_discount_batch({"discount_type": "X", "basis": "assessment", "mode": "percent", "value": 150}, [self.a1])

    def test_summary_report_filters_by_type_and_year(self):
        discounts.apply_discount_batch({"discount_type": "Test Sibling", "basis": "balance", "mode": "fixed", "value": 100}, [self.a1])
        discounts.apply_discount_batch({"discount_type": "Test Other", "basis": "assessment", "mode": "fixed", "value": 50}, [self.a2])
        _cols, data = discount_summary.execute({"discount_type": "Test Sibling"})
        self.assertEqual([r.discount_type for r in data], ["Test Sibling"])
        year = frappe.db.get_value("Academic Term", frappe.db.get_value("Enrollment Assessment", self.a1, "academic_term"), "school_year")
        self.assertEqual(len(discount_summary.execute({"school_year": year})[1]), 2)
        self.assertEqual(len(discount_summary.execute({"school_year": "1999-2000"})[1]), 0)


class TestGradeReport(FrappeTestCase):
    def test_report_final_grade_matches_the_rule(self):
        _cols, data = student_grade_report.execute({})
        self.assertTrue(data, "run the demo seed first")
        for row in data:
            grades = {q: row[q] for q in logic.QUARTERS if row[q] is not None}
            self.assertEqual(row["remarks"], logic.final_grade(grades)["remarks"])
            self.assertEqual(row["student_name"], frappe.db.get_value("BEd Student", row["student"], "student_name"))
