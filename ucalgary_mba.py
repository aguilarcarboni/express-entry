"""
Single-file UCalgary Full-Time MBA helper.

Values come from the selected profile in config.py (REAL / IDEAL).
Run:
    python ucalgary_mba.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple

from config import (
    MBA_APPLICANT_TYPE as APPLICANT_TYPE,
    MBA_DOCUMENTS as DOCUMENTS,
    MBA_GMAT_SCORE as GMAT_SCORE,
    MBA_GPA_LAST_TWO_YEARS as GPA_LAST_TWO_YEARS,
    MBA_GRE_QUANT as GRE_QUANT,
    MBA_GRE_VERBAL as GRE_VERBAL,
    MBA_HAS_FOUR_YEAR_DEGREE as HAS_FOUR_YEAR_DEGREE,
    IELTS as IELTS,
    MBA_INTAKE as INTAKE,
    MBA_INTAKE_YEAR as INTAKE_YEAR,
    MBA_NATIVE_ENGLISH as NATIVE_ENGLISH,
    MBA_WORK_YEARS as WORK_YEARS,
    ENGLISH_EXAM_DONE as ENGLISH_EXAM_DONE,
)
from language_utils import clb_stats, ielts_to_clb

# =============== 2) CONSTANTS & LOOKUPS ===============
GPA_MIN = 3.0
WORK_YEARS_MIN = 2
GMAT_RECOMMENDED = 550
GRE_RECOMMENDED = (155, 155)  # verbal, quantitative — "high scores" guideline

IELTS_COMPONENT_MIN = 6.0

DEADLINES = {
    "september": {
        "domestic": {"full_time": (6, 1)},  # June 1
        "international": {"full_time": (3, 1)},  # March 1
    },
    "january": {
        "domestic": {"accelerated": (11, 15)},  # Nov 15
        "international": {},
    },
}

SPECIALIZATIONS = [
    "Business Intelligence and Data Analytics",
    "Entrepreneurship and Innovation",
    "Finance",
    "Management Analytics",
    "Marketing",
    "Project Management",
    "Global Energy Management and Sustainable Development",
    "Real Estate Studies",
]

DOCUMENT_LABELS = {
    "resume": "Résumé",
    "essay_1": "Essay 1 (250 words)",
    "essay_2": "Essay 2 (250 words)",
    "reference_1": "Reference 1 (professional questionnaire)",
    "reference_2": "Reference 2 (professional questionnaire)",
    "transcripts": "Official transcripts",
}


# =============== 3) ELIGIBILITY CHECKS ===============
def gpa_ok(gpa: float) -> bool:
    return gpa >= GPA_MIN


def degree_ok(has_four_year_degree: bool) -> bool:
    return has_four_year_degree


def work_ok(years: int) -> bool:
    return years >= WORK_YEARS_MIN


def gmat_ok(score: int | None) -> bool:
    return score is not None and score >= GMAT_RECOMMENDED


def gre_ok(verbal: int | None, quant: int | None) -> bool:
    return (
        verbal is not None
        and quant is not None
        and verbal >= GRE_RECOMMENDED[0]
        and quant >= GRE_RECOMMENDED[1]
    )


def english_ok(native: bool, exam_done: bool, bands: Dict[str, float]) -> Tuple[bool, str]:
    if native:
        return True, "Waived (native English)"

    if not exam_done:
        return False, "English exam not taken"

    if not bands:
        return False, f"IELTS band scores missing (need ≥ {IELTS_COMPONENT_MIN} in all four skills)"

    too_low = {k: v for k, v in bands.items() if v < IELTS_COMPONENT_MIN}
    if too_low:
        desc = ", ".join(f"{k}:{v}" for k, v in too_low.items())
        return False, f"IELTS bands below {IELTS_COMPONENT_MIN}: {desc}"

    return True, "IELTS meets minimums (bands only, no overall required)"


def test_score_ok(gmat: int | None, gre_v: int | None, gre_q: int | None) -> Tuple[bool, str]:
    if gmat_ok(gmat):
        return True, f"GMAT {gmat} (recommended ≥ {GMAT_RECOMMENDED})"
    if gre_ok(gre_v, gre_q):
        return True, f"GRE V{gre_v}/Q{gre_q} (recommended high verbal + quant)"
    return False, "GMAT/GRE missing or below recommended threshold"


def deadline_for(intake: str, applicant_type: str, year: int) -> date | None:
    intake_key = intake.lower()
    applicant_key = applicant_type.lower()
    month_day = DEADLINES.get(intake_key, {}).get(applicant_key, {}).get("full_time")
    if not month_day:
        return None
    month, day_num = month_day
    return date(year, month, day_num)


def days_until(target: date | None) -> int | None:
    if not target:
        return None
    return (target - date.today()).days


@dataclass
class Eligibility:
    eligible: bool
    checks: Dict[str, bool]
    notes: Dict[str, str]
    issues: List[str]


def evaluate() -> Eligibility:
    checks = {
        "gpa": gpa_ok(GPA_LAST_TWO_YEARS),
        "degree": degree_ok(HAS_FOUR_YEAR_DEGREE),
        "work": work_ok(WORK_YEARS),
    }

    test_ok, test_note = test_score_ok(GMAT_SCORE, GRE_VERBAL, GRE_QUANT)
    checks["test"] = test_ok

    english_okay, english_note = english_ok(NATIVE_ENGLISH, ENGLISH_EXAM_DONE, IELTS)
    checks["english"] = english_okay

    docs_ok = all(DOCUMENTS.values())
    checks["documents"] = docs_ok

    missing_docs = [DOCUMENT_LABELS.get(k, k) for k, v in DOCUMENTS.items() if not v]
    documents_note = "See individual document checklist below" if docs_ok else "Missing: " + ", ".join(missing_docs)

    notes = {
        "test": test_note,
        "english": english_note,
        "documents": documents_note,
    }

    issues: List[str] = []
    for label, passed in checks.items():
        if not passed:
            issues.append(label)

    return Eligibility(
        eligible=not issues,
        checks=checks,
        notes=notes,
        issues=issues,
    )


# =============== 4) ACTIONABLE NEXT STEPS ===============
def actions(el: Eligibility) -> List[str]:
    items: List[str] = []
    if not el.checks["gpa"]:
        items.append("GPA: aim for ≥3.0 in remaining courses or consider academic upgrade")
    if not el.checks["degree"]:
        items.append("Education: ensure a four-year bachelor's (or equivalent) credential")
    if not el.checks["work"]:
        items.append(f"Work experience: accumulate at least {WORK_YEARS_MIN} years appropriate full-time work")
    if not el.checks["test"]:
        items.append(f"Test: target GMAT {GMAT_RECOMMENDED}+ or GRE verbal/quant at strong scores")
    if not el.checks["english"]:
        items.append(f"English: complete IELTS and ensure all bands ≥ {IELTS_COMPONENT_MIN}")
    if not el.checks["documents"]:
        items.append("Documents: prepare " + ", ".join([DOCUMENT_LABELS.get(k, k) for k, v in DOCUMENTS.items() if not v]))
    if not items:
        items.append("All key requirements met; proceed to application portal and submit early")
    return items


# =============== 5) RENDER OUTPUT ===============
def render():
    el = evaluate()
    deadline = deadline_for(INTAKE, APPLICANT_TYPE, INTAKE_YEAR)
    days_left = days_until(deadline)
    english_clb = ielts_to_clb(IELTS) if IELTS else {}

    print("=== UCalgary Full-Time MBA Checklist ===\n")

    print(f"Intake: {INTAKE.title()} {INTAKE_YEAR} (full-time)")
    if deadline:
        when = deadline.isoformat()
        deadline_line = f"{when}"
        if days_left is not None:
            deadline_line += f" ({days_left} days remaining)"
        print(f"Deadline: {deadline_line}")
    else:
        print("Deadline: N/A for selected intake/applicant type")
    print()

    if ENGLISH_EXAM_DONE:
        print(f"English Score: ")
        print("Breakdown:")
        print(f"- Listening: {english_clb['listening']}")
        print(f"- Reading: {english_clb['reading']}")
        print(f"- Writing: {english_clb['writing']}")
        print(f"- Speaking: {english_clb['speaking']}")
    else:
        print("English exam not taken")
    print()

    # Eligibility section laid out like express_entry.
    print(f"Eligibility: {'PASS' if el.eligible else 'CHECK REQUIREMENTS'}")
    print()

    print("Checklist:")
    checklist = [
        ("Four-year degree", el.checks["degree"]),
        (f"GPA: {GPA_LAST_TWO_YEARS} ≥ 3.0", el.checks["gpa"]),
        ("Work experience ≥ 2 years", el.checks["work"]),
        (f"GMAT score ≥ {GMAT_RECOMMENDED}", el.checks["test"]),
        (f"IELTS bands ≥ {IELTS_COMPONENT_MIN} in all skills", el.checks["english"]),
        ("Resume", DOCUMENTS["resume"]),
        ("Essay 1", DOCUMENTS["essay_1"]),
        ("Essay 2", DOCUMENTS["essay_2"]),
        ("Reference 1", DOCUMENTS["reference_1"]),
        ("Reference 2", DOCUMENTS["reference_2"]),
        ("Transcripts", DOCUMENTS["transcripts"]),
    ]
    for label, status in checklist:
        mark = "✅" if status else "❌"
        print(f"{mark} {label}")
    print()

if __name__ == "__main__":
    render()

