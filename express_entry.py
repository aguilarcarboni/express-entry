"""
Express Entry helper.

Edit values in config.py, then run:
    python express_entry.py

Pure functions, no persistence, no CLI flags. Python 3.11+
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import (
    AGE,
    CANADIAN_EDUCATION,
    EDUCATION,
    ENGLISH_EXAM_DONE,
    FOREIGN_WORK_YEARS,
    FRENCH_EXAM_DONE,
    IELTS,
    JOB_OFFER,
    PASSPORT_VALID,
    PNP,
    PROOF_OF_FUNDS_CAD,
    PROOF_OF_WORK,
    ECA_DONE,
    POLICE_CERTIFICATES_DONE,
    RELATIVE_IN_CANADA,
    TCF,
)
from conversion_tables import IELTS_CLB_TABLE, TCF_NCLC_TABLE
from language_utils import (
    clb_stats,
    ielts_to_clb,
    next_clb_target,
    next_relevant_french_target,
    tcf_to_nclc,
    zero_clb,
)

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
        print(f"English Score: ")
        print("Breakdown:")
        print(f"- Listening: {english_clb['listening']}")
        print(f"- Reading: {english_clb['reading']}")
        print(f"- Writing: {english_clb['writing']}")
        print(f"- Speaking: {english_clb['speaking']}")
    else:
        print("English exam not taken")

    print()
    if FRENCH_EXAM_DONE:
        print(f"French Score: ")
        print("Breakdown:")
        print(f"- Listening: {french_clb['listening']}")
        print(f"- Reading: {french_clb['reading']}")
        print(f"- Writing: {french_clb['writing']}")
        print(f"- Speaking: {french_clb['speaking']}")
    else:
        print("French exam not taken")

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
    print()

    print(f"CRS Score: {crs.total}")
    print("Breakdown:")
    for label in ["age", "education", "english", "french", "foreign_work"]:
        print(f"- {label.replace('_', ' ').title()}: {crs.breakdown[label]}")
    print(f"- Transferability: {crs.transfer_total}")
    print(f"- Bonus: {crs.bonus_total}\n")

    print("CRS Actionable Improvements:")
    actions = [
        delta_english_next_clb(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_french_next_clb(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_education_next_level(EDUCATION, english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_plus_one_year_work(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, CANADIAN_EDUCATION, JOB_OFFER),
        delta_pnp(english_clb, french_clb, FOREIGN_WORK_YEARS, JOB_OFFER),
        delta_canadian_education(english_clb, french_clb, FOREIGN_WORK_YEARS, PNP, JOB_OFFER),
    ]
    for action in actions:
        print(f"+{action['delta']} -> {action['new_crs']} | {action['condition']}")
    print()
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
        ("Passport valid ≥ 6 months on application", PASSPORT_VALID),
        ("IELTS taken", ENGLISH_EXAM_DONE),
        ("TCF taken", FRENCH_EXAM_DONE),
        (f"FSW: {fsw['total']} > 67", fsw["pass"]),
        (f"CRS: {crs.total} > 500", crs.total >= 500),
        ("Proof of work experience (AGM)", PROOF_OF_WORK),
        ("Proof of funds (Conape)", proof_of_funds_ok(PROOF_OF_FUNDS_CAD, family_size=1)),
        ("Eletronic Credential Assessment (ECA)", ECA_DONE),
        ("Police certificates", POLICE_CERTIFICATES_DONE),
    ]
    for label, status in checklist:
        mark = "✅" if status else "❌"
        print(f"{mark} {label}")
    print()

if __name__ == "__main__":
    render()
