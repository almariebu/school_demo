"""Pure business rules for School Demo.

This module must NOT import frappe. Controllers call these functions and turn
``LogicError`` into ``frappe.throw``. That keeps the rules testable with plain
``unittest`` on any machine, without a bench or a database.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Optional, Sequence


class LogicError(ValueError):
    """Raised when a business rule is violated."""


# ----------------------------------------------------------------- constants
GRADE_LEVELS = ("Kinder",) + tuple(f"Grade {i}" for i in range(1, 13))
SENIOR_HIGH_GRADES = ("Grade 11", "Grade 12")
TEACHER_ROLE = "Teacher"
TEACHER_PRIVILEGED_ROLES = frozenset({"System Manager", "Registrar", "Dean"})


def flt(value, precision: Optional[int] = None) -> float:
    """Forgiving float conversion (None / '' / junk -> 0.0)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return round(number, precision) if precision is not None else number


# ------------------------------------------------- case 1: units and fees
def total_units(units: Iterable) -> float:
    return round(sum(flt(u) for u in units), 2)


def check_unit_limit(total: float, max_units: float) -> float:
    """Raise if ``total`` exceeds the term limit. A limit of 0 means unlimited."""
    total, limit = flt(total), flt(max_units)
    if limit > 0 and total > limit + 1e-9:
        raise LogicError(f"Total of {total:g} units exceeds the {limit:g}-unit limit for this term.")
    return total


def compute_fee_totals(units: float, tuition_per_unit: float, misc_amounts: Iterable) -> dict:
    tuition = round(flt(units) * flt(tuition_per_unit), 2)
    misc = round(sum(flt(a) for a in misc_amounts), 2)
    return {"tuition_total": tuition, "misc_total": misc, "total_fees": round(tuition + misc, 2)}


def check_downpayment(paid: float, required: float) -> bool:
    """The Finance gate: paid down payment must cover the required amount."""
    paid, required = round(flt(paid), 2), round(flt(required), 2)
    if paid < required:
        raise LogicError(
            f"Down payment of {paid:,.2f} is below the required {required:,.2f}. "
            "Record and submit a Student Payment first."
        )
    return True


def payment_status(paid: float, required: float, total_fees: float) -> str:
    paid, required, total_fees = flt(paid), flt(required), flt(total_fees)
    if paid <= 0:
        return "Unpaid"
    if total_fees > 0 and paid >= total_fees:
        return "Fully Paid"
    if paid >= required:
        return "Down Payment Met"
    return "Partial"


# ------------------------------------- case 1: normalization / idempotency
_LOWER_PARTICLES = {"de", "la", "ng", "y", "van", "von"}
_SUFFIXES = {"jr": "Jr.", "sr": "Sr.", "ii": "II", "iii": "III", "iv": "IV"}


def _cap_token(token: str) -> str:
    parts = re.split(r"([-'])", token)
    return "".join(p if p in ("-", "'") else p.capitalize() for p in parts)


def normalize_name(value) -> str:
    """'  MA. cristina  dela cRUZ ' -> 'Ma. Cristina Dela Cruz'."""
    if not value:
        return ""
    tokens = re.sub(r"\s+", " ", str(value)).strip().split(" ")
    out = []
    for i, token in enumerate(tokens):
        key = token.lower().rstrip(".")
        if i > 0 and key in _SUFFIXES:
            out.append(_SUFFIXES[key])
        elif i > 0 and key in _LOWER_PARTICLES:
            out.append(key)
        else:
            out.append(_cap_token(token))
    return " ".join(out)


def normalize_mobile(value) -> str:
    """Philippine mobile numbers -> +639XXXXXXXXX. Returns '' when not valid."""
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 12 and digits.startswith("63"):
        national = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        national = digits[1:]
    elif len(digits) == 10:
        national = digits
    else:
        return ""
    return "+63" + national if national.startswith("9") else ""


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value) -> str:
    email = str(value or "").strip().lower()
    return email if _EMAIL_RE.match(email) else ""


def build_student_payload(applicant: Optional[Mapping], existing: Optional[Mapping] = None) -> dict:
    """Normalize applicant data into an Enrolled Student payload.

    Never blanks a value: when the applicant record is missing or has bad data
    for a field, the existing student value is kept. That makes re-running the
    enrollment safe (no wipe, no duplicate).
    """
    applicant = applicant or {}
    existing = existing or {}
    parts = [normalize_name(applicant.get(k)) for k in ("first_name", "middle_name", "last_name")]
    fresh = {
        "student_name": " ".join(p for p in parts if p) or normalize_name(applicant.get("full_name")),
        "email": normalize_email(applicant.get("email")),
        "mobile": normalize_mobile(applicant.get("mobile")),
        "birth_date": applicant.get("birth_date"),
        "gender": applicant.get("gender"),
        "program": applicant.get("program"),
        "academic_term": applicant.get("academic_term"),
    }
    merged = {}
    for key, value in fresh.items():
        if value not in (None, ""):
            merged[key] = value
        elif existing.get(key) not in (None, ""):
            merged[key] = existing[key]
    return merged


# --------------------------------------------------- scheduling (case 1)
def to_minutes(value) -> int:
    """Accepts 'HH:MM[:SS]', datetime.time or datetime.timedelta."""
    if value is None or value == "":
        raise LogicError("Time is required.")
    if hasattr(value, "total_seconds"):
        return int(value.total_seconds() // 60)
    if hasattr(value, "hour") and hasattr(value, "minute"):
        return value.hour * 60 + value.minute
    match = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$", str(value).strip())
    if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
        raise LogicError(f"Invalid time: {value}")
    return int(match.group(1)) * 60 + int(match.group(2))


def check_time_range(start, end) -> tuple:
    s, e = to_minutes(start), to_minutes(end)
    if e <= s:
        raise LogicError("End time must be after start time.")
    return s, e


def times_overlap(start1, end1, start2, end2) -> bool:
    return to_minutes(start1) < to_minutes(end2) and to_minutes(start2) < to_minutes(end1)


# ------------------------------------------- case 2: basic education
def is_senior_high(grade_level: str) -> bool:
    return grade_level in SENIOR_HIGH_GRADES


def next_grade_level(current: str) -> str:
    if current not in GRADE_LEVELS:
        raise LogicError(f"Unknown grade level: {current!r}")
    index = GRADE_LEVELS.index(current)
    if index == len(GRADE_LEVELS) - 1:
        raise LogicError("Grade 12 completers cannot be promoted further.")
    return GRADE_LEVELS[index + 1]


def resolve_grade_level(enrollment_type: str, incoming: Optional[str], last_grade: Optional[str]) -> str:
    """New keeps the incoming grade; Continuing moves up one from the last enrollment."""
    if enrollment_type == "New":
        if incoming not in GRADE_LEVELS:
            raise LogicError("Select the incoming grade level for a new student.")
        return incoming
    if enrollment_type == "Continuing":
        if not last_grade:
            raise LogicError("No previous active enrollment found. Use enrollment type New instead.")
        return next_grade_level(last_grade)
    raise LogicError(f"Unknown enrollment type: {enrollment_type!r}")


def active_key(student: str, academic_year: str, status: str, docstatus: int) -> Optional[str]:
    """Value for the unique `active_key` column. None (NULL) releases the slot."""
    if status == "Active" and docstatus in (0, 1) and student and academic_year:
        return f"{student}|{academic_year}"
    return None


def withdrawal_plan(grade_level: str) -> dict:
    """What a withdrawal must clear. Senior high also clears leftover Student Grade rows."""
    return {"clear_class_list": True, "clear_student_grades": is_senior_high(grade_level)}


def check_lrn(lrn) -> str:
    value = re.sub(r"\s", "", str(lrn or ""))
    if value and not re.fullmatch(r"\d{12}", value):
        raise LogicError("LRN must be exactly 12 digits.")
    return value


def check_grade(grade) -> float:
    value = flt(grade)
    if value < 0 or value > 100:
        raise LogicError("Grade must be between 0 and 100.")
    return value


# --------------------------------------------------------- permissions
def is_teacher_restricted(roles: Iterable[str]) -> bool:
    roles = set(roles or [])
    return TEACHER_ROLE in roles and not (roles & TEACHER_PRIVILEGED_ROLES)


def teacher_can_access(roles: Iterable[str], user: str, assigned_to: Optional[str]) -> bool:
    if not is_teacher_restricted(roles):
        return True
    return bool(assigned_to) and assigned_to == user


# ------------------------------------------------------------- reporting
def state_fieldname(state: str) -> str:
    return re.sub(r"\W+", "_", state.lower()).strip("_")


def pivot_counts(rows: Sequence[Mapping], states: Sequence[str], key: str = "academic_term") -> list:
    """rows: [{key, workflow_state, cnt}] -> one dict per key with a column per state."""
    table: dict = {}
    for row in rows:
        entry = table.setdefault(row[key], {key: row[key], **{state_fieldname(s): 0 for s in states}, "total": 0})
        field = state_fieldname(row.get("workflow_state") or "Draft")
        entry[field] = entry.get(field, 0) + int(row["cnt"])
        entry["total"] += int(row["cnt"])
    return [table[k] for k in sorted(table, reverse=True)]
