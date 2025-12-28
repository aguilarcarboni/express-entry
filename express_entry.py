"""
Single-file Express Entry helper.

Edit the user input block below, then run:
    python express_entry.py

Pure functions, no persistence, no CLI flags.
Python 3.11+
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# =============== 1) USER INPUTS (edit these) ===============
AGE = 23

EDUCATION = "bachelor"  # options in EDUCATION_LEVELS below

FOREIGN_WORK_YEARS = 2  # full-time equivalent, foreign only

IELTS = {
    "listening": 8.0,
    "reading": 8.0,
    "writing": 8.0,
    "speaking": 8.0,
}

TCF = {
    "listening": 150,
    "reading": 150,
    "writing": 3,
    "speaking": 3,
}

ENGLISH_EXAM_DONE = True  # set to False if the English test is not yet taken
FRENCH_EXAM_DONE = False  # set to False if the French test is not yet taken

PROOF_OF_FUNDS_CAD = 0

PNP = False
CANADIAN_EDUCATION = False
RELATIVE_IN_CANADA = True  # eligible close relative (e.g., aunt/uncle) for FSW adaptability
JOB_OFFER = None  # Options: None, "teer00" (200 pts), "teer123" (50 pts)

# =============== 2) LANGUAGE CONVERSION TABLES ===============
# IELTS General Training -> CLB thresholds (score >= threshold)
IELTS_CLB_TABLE: Dict[str, List[Tuple[float, int]]] = {
    "listening": [(8.5, 10), (8.0, 9), (7.5, 8), (6.0, 7), (5.5, 6), (5.0, 5), (4.5, 4)],
    "reading": [(8.0, 10), (7.0, 9), (6.5, 8), (6.0, 7), (5.0, 6), (4.0, 5), (3.5, 4)],
    "writing": [(7.5, 10), (7.0, 9), (6.5, 8), (6.0, 7), (5.5, 6), (5.0, 5), (4.0, 4)],
    "speaking": [(7.5, 10), (7.0, 9), (6.5, 8), (6.0, 7), (5.5, 6), (5.0, 5), (4.0, 4)],
}

# TCF Canada -> NCLC thresholds
TCF_NCLC_TABLE: Dict[str, List[Tuple[float, int]]] = {
    "listening": [(549, 10), (523, 9), (503, 8), (458, 7), (398, 6), (369, 5), (331, 4)],
    "reading": [(549, 10), (524, 9), (499, 8), (453, 7), (406, 6), (375, 5), (342, 4)],
    "writing": [(16, 10), (14, 9), (12, 8), (10, 7), (9, 6), (7, 5), (6, 4)],
    "speaking": [(16, 10), (14, 9), (12, 8), (10, 7), (9, 6), (7, 5), (6, 4)],
}

# =============== 3) CONSTANTS & LOOKUPS ===============
EDUCATION_LEVELS = {
    "less_than_secondary",
    "secondary",
    "one_year_post_secondary",
    "two_year_post_secondary",
    "bachelor",  # three years or longer
    "two_or_more",  # two or more creds, one 3+ years
    "masters",
    "professional_degree",  # entry-to-practice (MD, DDS, PharmD, etc.)
    "phd",
}

EDUCATION_ORDER = [
    "less_than_secondary",
    "secondary",
    "one_year_post_secondary",
    "two_year_post_secondary",
    "bachelor",
    "two_or_more",
    "masters",
    "professional_degree",
    "phd",
]

FSW_AGE_POINTS = {
    **{age: 12 for age in range(18, 36)},
    36: 11,
    37: 10,
    38: 9,
    39: 8,
    40: 7,
    41: 6,
    42: 5,
    43: 4,
    44: 3,
    45: 2,
    46: 1,
    47: 0,
}

FSW_EDU_POINTS = {
    "phd": 25,
    "masters": 23,
    "professional_degree": 23,
    "two_or_more": 22,
    "bachelor": 21,
    "two_year_post_secondary": 19,
    "one_year_post_secondary": 15,
    "secondary": 5,
    "less_than_secondary": 0,
}

FSW_WORK_POINTS = {
    0: 0,
    1: 9,
    2: 11,  # 2-3 years
    3: 11,
    4: 13,  # 4-5 years
    5: 13,
    6: 15,  # 6+ years
}

CRS_AGE_POINTS = {
    17: 0,
    18: 99,
    19: 105,
    **{age: 110 for age in range(20, 30)},  # 20-29
    30: 105,
    31: 99,
    32: 94,
    33: 88,
    34: 83,
    35: 77,
    36: 72,
    37: 66,
    38: 61,
    39: 55,
    40: 50,
    41: 39,
    42: 28,
    43: 17,
    44: 6,
    45: 0,
    46: 0,
    47: 0,
}

CRS_EDU_POINTS = {
    "less_than_secondary": 0,
    "secondary": 30,
    "one_year_post_secondary": 90,
    "two_year_post_secondary": 98,
    "bachelor": 120,
    "two_or_more": 128,
    "masters": 135,
    "professional_degree": 135,
    "phd": 150,
}

FRENCH_THRESHOLDS = (5, 7, 9)

# Proof of funds (single applicant family size only; values in CAD).
# 2024 IRCC cut-offs; adjust manually if IRCC updates.
PROOF_OF_FUNDS = {
    1: 13857,
    2: 17254,
    3: 21206,
    4: 25724,
    5: 29053,
    6: 32701,
    7: 36399,
}

# =============== 2) LANGUAGE CONVERSION HELPERS ===============
def _convert_with_table(score: float, table: List[Tuple[float, int]]) -> int:
    for threshold, clb in table:
        if score >= threshold:
            return clb
    return 0


def zero_clb(table: Dict[str, List[Tuple[float, int]]]) -> Dict[str, int]:
    return {skill: 0 for skill in table}


def ielts_to_clb(scores: Dict[str, float]) -> Dict[str, int]:
    return {skill: _convert_with_table(scores.get(skill, 0.0), IELTS_CLB_TABLE[skill]) for skill in IELTS_CLB_TABLE}


def tcf_to_nclc(scores: Dict[str, float]) -> Dict[str, int]:
    return {skill: _convert_with_table(scores.get(skill, 0.0), TCF_NCLC_TABLE[skill]) for skill in TCF_NCLC_TABLE}


def clb_stats(clb_dict: Dict[str, int]) -> Tuple[float, int]:
    values = list(clb_dict.values())
    return sum(values) / len(values), min(values)


# =============== 3) FSW ELIGIBILITY ===============
def fsw_age(age: int) -> int:
    return FSW_AGE_POINTS.get(age, 0)


def fsw_education(level: str) -> int:
    if level not in EDUCATION_LEVELS:
        raise ValueError(f"Invalid education level: {level}")
    return FSW_EDU_POINTS.get(level, 0)


def fsw_language_primary(clb: Dict[str, int]) -> int:
    points = 0
    for level in clb.values():
        if level >= 9:
            points += 6
        elif level == 8:
            points += 5
        elif level == 7:
            points += 4
    return min(points, 24)


def fsw_language_secondary(clb: Dict[str, int]) -> int:
    points = sum(1 for level in clb.values() if level >= 5)
    return min(points, 4)


def fsw_work_experience(years: int) -> int:
    if years <= 0:
        return 0
    if years >= 6:
        return FSW_WORK_POINTS[6]
    if years >= 4:
        return FSW_WORK_POINTS[4]
    if years >= 2:
        return FSW_WORK_POINTS[2]
    return FSW_WORK_POINTS[1]


def fsw_adaptability(relative_in_canada: bool) -> int:
    return 5 if relative_in_canada else 0


def fsw_eligibility(age: int, education: str, primary_clb: Dict[str, int], secondary_clb: Dict[str, int], foreign_work_years: int, relative_in_canada: bool):
    if education not in EDUCATION_LEVELS:
        raise ValueError(f"Education level {education!r} not supported.")

    issues: List[str] = []
    if min(primary_clb.values()) < 7:
        issues.append("Primary language must be CLB 7+ in all abilities.")
    if foreign_work_years < 1:
        issues.append("At least 1 year of continuous full-time (or equivalent) foreign work is required.")

    age_pts = fsw_age(age)
    edu_pts = fsw_education(education)
    lang_primary_pts = fsw_language_primary(primary_clb)
    lang_secondary_pts = fsw_language_secondary(secondary_clb)
    work_pts = fsw_work_experience(foreign_work_years)
    arranged_employment = 0
    adaptability = fsw_adaptability(relative_in_canada)

    total = age_pts + edu_pts + lang_primary_pts + lang_secondary_pts + work_pts + arranged_employment + adaptability
    return {
        "total": total,
        "pass": total >= 67 and not issues,
        "breakdown": {
            "age": age_pts,
            "education": edu_pts,
            "language_primary": lang_primary_pts,
            "language_secondary": lang_secondary_pts,
            "foreign_work": work_pts,
            "arranged_employment": arranged_employment,
            "adaptability": adaptability,
        },
        "issues": issues,
    }


# =============== 4) CRS CORE ===============
def crs_age(age: int) -> int:
    if age < 17:
        return 0
    if age > 47:
        return 0
    return CRS_AGE_POINTS.get(age, CRS_AGE_POINTS[max(k for k in CRS_AGE_POINTS if k <= age)])


def crs_education(level: str) -> int:
    if level not in EDUCATION_LEVELS:
        raise ValueError(f"Invalid education level: {level}")
    return CRS_EDU_POINTS[level]


def crs_language_primary(clb: Dict[str, int]) -> int:
    score = 0
    for level in clb.values():
        if level >= 10:
            score += 34
        elif level == 9:
            score += 31
        elif level == 8:
            score += 23
        elif level == 7:
            score += 17
        elif level == 6:
            score += 9
        elif level == 5:
            score += 6
    return score


def crs_language_secondary(clb: Dict[str, int]) -> int:
    score = 0
    for level in clb.values():
        if level >= 9:
            score += 6
        elif level >= 7:
            score += 3
        elif level >= 5:
            score += 1
    return min(score, 24)


def crs_foreign_work(years: int) -> int:
    # Standalone foreign work is not a core CRS factor. We keep this for transparency and set to 0.
    return 0


# =============== 5) SKILL TRANSFERABILITY ===============
def _has_all_primary_at_least(clb: Dict[str, int], threshold: int) -> bool:
    return min(clb.values()) >= threshold


def transfer_education_language(education: str, primary_clb: Dict[str, int]) -> int:
    if not _has_all_primary_at_least(primary_clb, 7):
        return 0
    strong = _has_all_primary_at_least(primary_clb, 9)
    if education in {"less_than_secondary", "secondary"}:
        return 0
    if education in {"one_year_post_secondary", "two_year_post_secondary"}:
        return 25 if strong else 13
    if education in {"bachelor", "two_or_more", "masters", "professional_degree", "phd"}:
        return 50 if strong else 25
    return 0


def transfer_foreign_work_language(foreign_years: int, primary_clb: Dict[str, int]) -> int:
    if foreign_years < 1:
        return 0
    strong = _has_all_primary_at_least(primary_clb, 9)
    if not _has_all_primary_at_least(primary_clb, 7):
        return 0
    if foreign_years >= 3:
        return 50 if strong else 25
    if foreign_years >= 1:
        return 25 if strong else 13
    return 0


def skill_transferability(education: str, foreign_years: int, primary_clb: Dict[str, int]) -> Tuple[int, Dict[str, int]]:
    education_language = transfer_education_language(education, primary_clb)
    foreign_language = transfer_foreign_work_language(foreign_years, primary_clb)
    total = min(education_language + foreign_language, 100)
    return total, {
        "education_language": education_language,
        "foreign_work_language": foreign_language,
    }


# =============== 6) BONUS FACTORS ===============
def job_offer_points(job_offer: str | None) -> int:
    if job_offer == "teer00":
        return 200
    if job_offer == "teer123":
        return 50
    return 0


def bonus_points(primary_clb: Dict[str, int], french_clb: Dict[str, int], pnp: bool, canadian_education: bool, job_offer: str | None) -> Tuple[int, Dict[str, int]]:
    bonus = 0
    detail = {}
    if pnp:
        detail["pnp"] = 600
        bonus += 600
    else:
        detail["pnp"] = 0

    # French bonus (second official). Requires NCLC7+ in all skills.
    if min(french_clb.values()) >= 7:
        if _has_all_primary_at_least(primary_clb, 5):
            detail["french_bonus"] = 50
            bonus += 50
        else:
            detail["french_bonus"] = 25
            bonus += 25
    else:
        detail["french_bonus"] = 0

    if canadian_education:
        detail["canadian_education"] = 15
        bonus += 15
    else:
        detail["canadian_education"] = 0

    offer_pts = job_offer_points(job_offer)
    detail["job_offer"] = offer_pts
    bonus += offer_pts

    return bonus, detail


# =============== 7) ACTIONABLE DELTAS ===============
def next_clb_target(current: Dict[str, int], max_target: int = 10) -> Tuple[int, List[str]]:
    min_level = min(current.values())
    if min_level >= max_target:
        return min_level, []
    target = min(min_level + 1, max_target)
    gaps = [skill for skill, level in current.items() if level < target]
    return target, gaps


def next_relevant_french_target(french_clb: Dict[str, int]) -> Tuple[int | None, List[str]]:
    min_level = min(french_clb.values())
    for threshold in FRENCH_THRESHOLDS:
        if min_level < threshold:
            skills = [skill for skill, level in french_clb.items() if level < threshold]
            return threshold, skills
    return None, []


def next_education_level(current: str) -> str | None:
    if current not in EDUCATION_ORDER:
        raise ValueError(f"Education level {current!r} not supported.")
    idx = EDUCATION_ORDER.index(current)
    if idx >= len(EDUCATION_ORDER) - 1:
        return None
    return EDUCATION_ORDER[idx + 1]


@dataclass
class CRSResult:
    total: int
    core_total: int
    transfer_total: int
    bonus_total: int
    breakdown: Dict[str, int]
    transfer_detail: Dict[str, int]
    bonus_detail: Dict[str, int]


def compute_crs(english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, pnp: bool, canadian_education: bool, job_offer: str | None, education: str | None = None) -> CRSResult:
    edu_level = education or EDUCATION

    age_pts = crs_age(AGE)
    edu_pts = crs_education(edu_level)
    lang_primary_pts = crs_language_primary(english_clb)
    lang_secondary_pts = crs_language_secondary(french_clb)
    foreign_pts = crs_foreign_work(foreign_years)

    core_total = age_pts + edu_pts + lang_primary_pts + lang_secondary_pts + foreign_pts

    transfer_total, transfer_detail = skill_transferability(edu_level, foreign_years, english_clb)
    bonus_total, bonus_detail = bonus_points(english_clb, french_clb, pnp, canadian_education, job_offer)

    total = core_total + transfer_total + bonus_total
    breakdown = {
        "age": age_pts,
        "education": edu_pts,
        "english": lang_primary_pts,
        "french": lang_secondary_pts,
        "foreign_work": foreign_pts,
    }

    return CRSResult(
        total=total,
        core_total=core_total,
        transfer_total=transfer_total,
        bonus_total=bonus_total,
        breakdown=breakdown,
        transfer_detail=transfer_detail,
        bonus_detail=bonus_detail,
    )


def delta_english_next_clb(english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, pnp: bool, canadian_education: bool, job_offer: str | None) -> Dict[str, int | str]:
    target, skills = next_clb_target(english_clb)
    if not skills:
        return {"delta": 0, "new_crs": compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer).total, "condition": "English already at max CLB 10."}
    boosted = {skill: max(level, target) for skill, level in english_clb.items()}
    current_total = compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer).total
    new_total = compute_crs(boosted, french_clb, foreign_years, pnp, canadian_education, job_offer).total
    return {
        "delta": new_total - current_total,
        "new_crs": new_total,
        "condition": f"Reach CLB {target} in English for {', '.join(skills)}",
    }


def delta_french_next_clb(english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, pnp: bool, canadian_education: bool, job_offer: str | None) -> Dict[str, int | str]:
    target, skills = next_relevant_french_target(french_clb)
    if not target:
        return {"delta": 0, "new_crs": compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer).total, "condition": "French already at max NCLC 10."}
    boosted = {skill: max(level, target) for skill, level in french_clb.items()}
    current_total = compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer).total
    new_total = compute_crs(english_clb, boosted, foreign_years, pnp, canadian_education, job_offer).total
    return {
        "delta": new_total - current_total,
        "new_crs": new_total,
        "condition": f"Reach NCLC {target} in French for {', '.join(skills)}",
    }


def delta_education_next_level(education: str, english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, pnp: bool, canadian_education: bool, job_offer: str | None) -> Dict[str, int | str]:
    target_level = next_education_level(education)
    current_total = compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer, education=education).total
    if not target_level:
        return {
            "delta": 0,
            "new_crs": current_total,
            "condition": "Education already at highest level (phd).",
        }
    new_total = compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer, education=target_level).total
    return {
        "delta": new_total - current_total,
        "new_crs": new_total,
        "condition": f"Complete education upgrade: {education.replace('_', ' ')} -> {target_level.replace('_', ' ')}",
    }


def delta_plus_one_year_work(english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, pnp: bool, canadian_education: bool, job_offer: str | None) -> Dict[str, int | str]:
    current_total = compute_crs(english_clb, french_clb, foreign_years, pnp, canadian_education, job_offer).total
    if foreign_years >= 3:
        return {
            "delta": 0,
            "new_crs": current_total,
            "condition": "Foreign work already maxed for CRS (3+ years)",
        }
    new_years = foreign_years + 1
    new_total = compute_crs(english_clb, french_clb, new_years, pnp, canadian_education, job_offer).total
    return {
        "delta": new_total - current_total,
        "new_crs": new_total,
        "condition": f"Accumulate {new_years} years foreign work",
    }


def delta_pnp(english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, job_offer: str | None) -> Dict[str, int | str]:
    current_total = compute_crs(english_clb, french_clb, foreign_years, False, CANADIAN_EDUCATION, job_offer).total
    new_total = compute_crs(english_clb, french_clb, foreign_years, True, CANADIAN_EDUCATION, job_offer).total
    return {
        "delta": new_total - current_total,
        "new_crs": new_total,
        "condition": "Secure a provincial nomination (600 pts)",
    }


def delta_canadian_education(english_clb: Dict[str, int], french_clb: Dict[str, int], foreign_years: int, pnp: bool, job_offer: str | None) -> Dict[str, int | str]:
    current_total = compute_crs(english_clb, french_clb, foreign_years, pnp, False, job_offer).total
    new_total = compute_crs(english_clb, french_clb, foreign_years, pnp, True, job_offer).total
    return {
        "delta": new_total - current_total,
        "new_crs": new_total,
        "condition": "Complete eligible Canadian education (2+ years)",
    }


# =============== 8) WARNINGS & OUTPUT ===============
def proof_of_funds_ok(funds: float, family_size: int = 1) -> bool:
    required = PROOF_OF_FUNDS.get(family_size, PROOF_OF_FUNDS[7] + 3792 * (family_size - 7))
    return funds >= required


def render():
    english_clb_reference = ielts_to_clb(IELTS)
    french_clb_reference = tcf_to_nclc(TCF)

    english_clb = english_clb_reference if ENGLISH_EXAM_DONE else zero_clb(IELTS_CLB_TABLE)
    french_clb = french_clb_reference if FRENCH_EXAM_DONE else zero_clb(TCF_NCLC_TABLE)

    english_avg, english_min = clb_stats(english_clb)
    french_avg, french_min = clb_stats(french_clb)
    english_ref_avg, english_ref_min = clb_stats(english_clb_reference)
    french_ref_avg, french_ref_min = clb_stats(french_clb_reference)

    fsw = fsw_eligibility(AGE, EDUCATION, english_clb, french_clb, FOREIGN_WORK_YEARS, RELATIVE_IN_CANADA)
    crs = compute_crs(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER)

    print("=== EXPRESS ENTRY SUMMARY ===\n")

    if ENGLISH_EXAM_DONE:
        print(f"English")
        print(f"    Listening: {english_clb['listening']}")
        print(f"    Reading: {english_clb['reading']}")
        print(f"    Writing: {english_clb['writing']}")
        print(f"    Speaking: {english_clb['speaking']}")
    else:
        print("English")
        print("Exam not taken")

    print()
    if FRENCH_EXAM_DONE:
        print(f"French")
        print(f"    Listening: {french_clb['listening']}")
        print(f"    Reading: {french_clb['reading']}")
        print(f"    Writing: {french_clb['writing']}")
        print(f"    Speaking: {french_clb['speaking']}")
    else:
        print("French")
        print(f"Exam not taken")

    print()

    print(f"FSW Score: {'PASS' if fsw['pass'] else 'FAIL'} ({fsw['total']} / 100)")
    print("Breakdown:")
    for label in [
        "age",
        "education",
        "language_primary",
        "language_secondary",
        "foreign_work",
        "arranged_employment",
        "adaptability",
    ]:
        print(f"- {label.replace('_', ' ').title()}: {fsw['breakdown'][label]}")
    if fsw["issues"]:
        print("FSW requirements not met:")
        for issue in fsw["issues"]:
            print(f"- {issue}")
    print()
    print(f"CRS Score: {crs.total}")
    print("Breakdown:")
    for label in ["age", "education", "english", "french", "foreign_work"]:
        print(f"- {label.replace('_', ' ').title()}: {crs.breakdown[label]}")
    print(f"- Transferability: {crs.transfer_total}")
    print(f"- Bonus: {crs.bonus_total}\n")

    actions = [
        delta_english_next_clb(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_french_next_clb(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_education_next_level(EDUCATION, english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_plus_one_year_work(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_pnp(english_clb, french_clb, FOREIGN_WORK_YEARS, JOB_OFFER),
        delta_canadian_education(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, JOB_OFFER),
    ]

    warnings: List[str] = []
    if not proof_of_funds_ok(PROOF_OF_FUNDS_CAD, family_size=1):
        required = PROOF_OF_FUNDS[1]
        warnings.append(f"Proof of funds insufficient: need {required:,} CAD.")

    # Age drop notice (next birthday).
    next_age = AGE + 1
    current_age_pts = crs_age(AGE)
    next_age_pts = crs_age(next_age)
    if next_age_pts < current_age_pts:
        warnings.append(f"Turning {next_age} will reduce CRS age points by {current_age_pts - next_age_pts}.")

    print("Checklist:")
    checklist = [
        ("FSW eligible", fsw["pass"]),
        ("Passport valid ≥6 months on application", True),
        ("Language CLB/NCLC ≥ 7 primary", english_min >= 7),
        ("Proof of work experience (AGM)", False),
        ("Proof of funds (Conape)", proof_of_funds_ok(PROOF_OF_FUNDS_CAD, family_size=1)),
        ("Eletronic Credential Assessment (ECA)", False),
        ("Police certificates", False),
        ("Apply to college at University of Calgary", False),
        ("Get in contact with jobs in Calgary/Canada", False),
    ]
    for label, status in checklist:
        mark = "✔" if status else "✘"
        print(f"{mark} {label}")
    print()

    print("Actionable Improvements:")
    for action in actions:
        print(f"+{action['delta']} -> {action['new_crs']} | {action['condition']}")


if __name__ == "__main__":
    render()

