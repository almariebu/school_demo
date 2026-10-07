# School Demo

A public, installable **live demo** of two real school-system case studies by Almarie Bullo, built
on the **Frappe Framework v15** only (no ERPNext).

1. **College admission and enrollment**: Applicant, then Enrollment Assessment (subjects and fees,
   approved through a workflow), then Enrolled Student.
2. **Basic education enrollment**: Kinder to Grade 12 enrollment with grade promotion, one active
   enrollment per school year, a Withdraw action, class lists and teacher-only access.

All business rules live in [`school_demo/logic.py`](school_demo/logic.py), which has **no Frappe
imports**, so they are tested with plain `unittest` without a bench.

## What it demonstrates, and where

### Case study 1: College admission and enrollment

| Requirement | Implemented in |
| --- | --- |
| Applicant, then Enrollment Assessment, then Enrolled Student | DocTypes `applicant`, `enrollment_assessment`, `enrolled_student` under `school_demo/school_demo/doctype/` |
| Assessment is submittable with child tables | `enrollment_assessment.json` (`is_submittable`), child tables `assessment_subject`, `assessment_fee` |
| Masters: Academic Term, Program, Course Subject, Class Schedule, Fee Structure | `academic_term`, `program`, `course_subject`, `class_schedule`, `fee_structure` (+ child `fee_structure_item` for misc fees) |
| Class time editable after submit | `class_schedule.json`: `day`, `start_time`, `end_time`, `room`, `instructor` have `allow_on_submit`; re-checked in `ClassSchedule.before_update_after_submit` |
| Workflow Draft, Pending Dean, Pending Registrar, Pending Finance, Enrolled (locked), with Reject | `school_demo/fixtures/workflow.json` (+ `workflow_state.json`, `workflow_action_master.json`), loaded through `fixtures` in `hooks.py` |
| Roles Dean, Registrar, Finance Officer, Cashier | `school_demo/fixtures/role.json` |
| Finance cannot lock until the payment check passes | `EnrollmentAssessment.check_payment` (called from `validate` when state is Enrolled and from `before_submit`), rule in `logic.check_downpayment` |
| `Student Payment` (submittable), paid down payment >= required | DocType `student_payment`; sum of submitted payments in `EnrollmentAssessment.get_paid_amount`; requirement comes from `Fee Structure.required_downpayment` |
| Unit limit from the term's `max_units` | `EnrollmentAssessment.calculate_units`, rule in `logic.check_unit_limit` |
| Fees pulled per term, totals computed server-side | `EnrollmentAssessment.pull_term_rules` / `pull_fees`, math in `logic.compute_fee_totals`; client-sent units are ignored |
| Applicant errors do not propagate; enrollment is idempotent | `school_demo/enrollment.py::enroll_from_assessment` (get-or-update by applicant + term) and `logic.build_student_payload` (normalizes, never blanks existing data); `Applicant.normalize` only warns on bad contact data |

### Case study 2: Basic education enrollment

| Requirement | Implemented in |
| --- | --- |
| `BEd Enrollment` (submittable) with grade level, student, year, type | `doctype/bed_enrollment/` |
| New keeps incoming grade; Continuing moves up one (Kinder, Grade 1..12) | `BEdEnrollment.resolve_grade` and `get_last_enrollment`, rule in `logic.resolve_grade_level` / `logic.next_grade_level` |
| Block a second active enrollment for the same student and year | `BEdEnrollment.check_duplicate_active` (friendly message) plus the unique hidden column `active_key` (`logic.active_key`) as the hard guarantee |
| Withdraw action (whitelisted method + button) | `bed_enrollment.py::withdraw`, button in `bed_enrollment.js` |
| Withdraw clears class list rows, and Student Grade rows for Grade 11/12 | `withdraw` using `logic.withdrawal_plan` / `logic.is_senior_high` |
| Class List shows the student's current name | `ClassList.onload` and `refresh_student_names` (render time), plus `school_demo/events.py::refresh_student_names` wired as a `doc_events` hook on `BEd Student` (`on_update`, `after_rename`) |
| Teachers only see their own classes | `permission_query_conditions` and `has_permission` in `hooks.py`, implemented in `school_demo/permissions.py` for **Class List** and **Student Grade**; rule in `logic.is_teacher_restricted` / `logic.teacher_can_access` |

### Also included

| Item | Where |
| --- | --- |
| Script Report **Enrollment Pipeline** (counts per workflow state per term, with chart) | `school_demo/school_demo/report/enrollment_pipeline/`, pivot in `logic.pivot_counts` |
| Number Cards and **School Demo** workspace | `school_demo/school_demo/number_card/*`, `school_demo/school_demo/workspace/school_demo/school_demo.json` |
| Seed script `seed()` (idempotent) | `school_demo/setup/demo_data.py` |
| `after_install` seed, guarded by site config `school_demo_seed` | `school_demo/setup/install.py`, `hooks.py` |
| Daily wipe and reseed | `school_demo/setup/reset.py::reset_demo`, `scheduler_events` in `hooks.py` |
| Public landing page with demo logins | `school_demo/www/demo.html`, `demo.py` (served at `/demo`) |
| Docker and Frappe Cloud deployment | `deploy/docker-compose.yml`, `deploy/apps.json`, `deploy/build.sh`, `deploy/FRAPPE_CLOUD.md` |

## Install

Requirements: a bench running **Frappe version-15**.

```bash
bench get-app https://github.com/almariebu/school_demo --branch main
bench new-site demo.localhost            # skip if you already have a site
bench --site demo.localhost set-config school_demo_seed 1   # optional: seed on install
bench --site demo.localhost install-app school_demo
```

If you did not set `school_demo_seed` before installing, load the demo data manually (safe to repeat):

```bash
bench --site demo.localhost execute school_demo.setup.demo_data.seed
```

Then open `http://demo.localhost:8000/demo` for the landing page, or `/app/school-demo` for the workspace.

With `school_demo_seed` set, the scheduler runs `school_demo.setup.reset.reset_demo` daily, which wipes
the demo documents and reseeds them. Sites without the flag are never touched. To run it by hand:

```bash
bench --site demo.localhost execute school_demo.setup.reset.reset_demo --kwargs "{'force': True}"
```

Docker: see `deploy/docker-compose.yml`. Frappe Cloud: see `deploy/FRAPPE_CLOUD.md`.
Free self-hosting on Oracle Cloud Always Free (ARM): see [`deploy/oracle/ORACLE_CLOUD.md`](deploy/oracle/ORACLE_CLOUD.md).

## Demo logins

Password for all accounts: `demo1234`

| Login | Role | Try this |
| --- | --- | --- |
| `dean@demo.local` | Dean | Approve or reject assessments in Pending Dean |
| `registrar@demo.local` | Registrar | Create an assessment, exceed the unit limit, enroll a Continuing BEd student, press Withdraw |
| `finance@demo.local` | Finance Officer | Try Enroll on a Pending Finance assessment with a short down payment (blocked), then a paid one |
| `cashier@demo.local` | Cashier | Submit a Student Payment for the under-paid assessment |
| `teacher@demo.local` | Teacher | See only your own Class Lists and Student Grades |
| `teacher2@demo.local` | Teacher | A second adviser, to compare what each teacher sees |

## Tests

Pure business rules (no bench needed):

```bash
python3 -m unittest tests.test_logic -v
```

Use the explicit module name: a bare `python3 -m unittest` also discovers the DocType tests, which
need Frappe.

DocType tests (`FrappeTestCase`, need a bench and a test site):

```bash
bench --site demo.localhost run-tests --app school_demo
```

## Layout

```
school_demo/
  hooks.py  modules.txt  patches.txt  logic.py  enrollment.py  events.py  permissions.py
  fixtures/        roles, workflow states, workflow actions, workflow
  school_demo/     module: doctype/, report/, number_card/, workspace/
  setup/           demo_data.py (seed), reset.py (daily reset), install.py, demo_constants.py
  www/             demo.html + demo.py (public landing page)
  tests/utils.py   factories for the FrappeTestCase tests
tests/test_logic.py   plain unittest for logic.py
deploy/               docker-compose, apps.json, build.sh, FRAPPE_CLOUD.md, oracle/ (Oracle Cloud guide + setup.sh)
```

## License

MIT, see `license.txt`.
