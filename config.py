"""
User-editable configuration for the Express Entry helper.

You can now toggle between two profiles:
- real: your current situation.
- ideal: optimistic scenario (good scores, exams done).
Set PROFILE below to switch without touching the rest of the code.
"""

from __future__ import annotations

from typing import Dict, Literal, TypedDict


class Scenario(TypedDict):
    AGE: int
    EDUCATION: str
    FOREIGN_WORK_YEARS: int
    IELTS: Dict[str, float]
    TCF: Dict[str, float]
    ENGLISH_EXAM_DONE: bool
    FRENCH_EXAM_DONE: bool
    PROOF_OF_FUNDS_CAD: float
    PROOF_OF_WORK: bool
    ECA_DONE: bool
    POLICE_CERTIFICATES_DONE: bool
    PASSPORT_VALID: bool
    PNP: bool
    CANADIAN_EDUCATION: bool
    RELATIVE_IN_CANADA: bool
    JOB_OFFER: str | None
    # UCalgary MBA profile fields
    MBA_APPLICANT_TYPE: str  # "domestic" | "international"
    MBA_INTAKE: str
    MBA_INTAKE_YEAR: int
    MBA_GPA_LAST_TWO_YEARS: float
    MBA_HAS_FOUR_YEAR_DEGREE: bool
    MBA_WORK_YEARS: int
    MBA_GMAT_SCORE: int | None
    MBA_GRE_VERBAL: int | None
    MBA_GRE_QUANT: int | None
    MBA_NATIVE_ENGLISH: bool
    MBA_IELTS: Dict[str, float]
    MBA_DOCUMENTS: Dict[str, bool]


PROFILE: Literal["real", "ideal"] = "real"

REAL: Scenario = {
    "AGE": 23,
    "EDUCATION": "secondary",  # options in express_entry.EDUCATION_LEVELS
    "FOREIGN_WORK_YEARS": 2,  # full-time equivalent, foreign only
    "IELTS": {
        "listening": 8.0,
        "reading": 8.0,
        "writing": 8.0,
        "speaking": 8.0,
    },
    "TCF": {
        "listening": 150,
        "reading": 150,
        "writing": 3,
        "speaking": 3,
    },
    "ENGLISH_EXAM_DONE": False,  # set to False if the English test is not yet taken
    "FRENCH_EXAM_DONE": False,  # set to False if the French test is not yet taken
    "PROOF_OF_FUNDS_CAD": 0,
    "PROOF_OF_WORK": False,
    "ECA_DONE": False,
    "POLICE_CERTIFICATES_DONE": False,
    "PASSPORT_VALID": True,
    "PNP": False,
    "CANADIAN_EDUCATION": False,
    "RELATIVE_IN_CANADA": True,
    "JOB_OFFER": None,
    "MBA_APPLICANT_TYPE": "international",
    "MBA_INTAKE": "september",
    "MBA_INTAKE_YEAR": 2025,
    "MBA_GPA_LAST_TWO_YEARS": 3.07,
    "MBA_HAS_FOUR_YEAR_DEGREE": False,
    "MBA_WORK_YEARS": 2,
    "MBA_GMAT_SCORE": None,
    "MBA_GRE_VERBAL": None,
    "MBA_GRE_QUANT": None,
    "MBA_NATIVE_ENGLISH": False,
    "MBA_DOCUMENTS": {
        "resume": True,
        "essay_1": False,
        "essay_2": False,
        "reference_1": False,
        "reference_2": False,
        "transcripts": True,
    },
}

# Adjust the values below to your definition of "ideal".
IDEAL: Scenario = {
    "AGE": 23,
    "EDUCATION": "bachelor",
    "FOREIGN_WORK_YEARS": 3,
    "IELTS": {
        "listening": 8.0,
        "reading": 8.0,
        "writing": 8.0,
        "speaking": 8.0,
    },
    "TCF": {
        "listening": 330,
        "reading": 330,
        "writing": 8,
        "speaking": 8,
    },
    "ENGLISH_EXAM_DONE": True,
    "FRENCH_EXAM_DONE": True,
    "PROOF_OF_FUNDS_CAD": 17000,
    "PROOF_OF_WORK": True,
    "ECA_DONE": True,
    "POLICE_CERTIFICATES_DONE": True,
    "PASSPORT_VALID": True,
    "PNP": False,
    "CANADIAN_EDUCATION": False,
    "RELATIVE_IN_CANADA": True,
    "JOB_OFFER": None,
    # UCalgary MBA profile (optimistic)
    "MBA_APPLICANT_TYPE": "international",
    "MBA_INTAKE": "september",
    "MBA_INTAKE_YEAR": 2025,
    "MBA_GPA_LAST_TWO_YEARS": 3.7,
    "MBA_HAS_FOUR_YEAR_DEGREE": True,
    "MBA_WORK_YEARS": 3,
    "MBA_GMAT_SCORE": 660,
    "MBA_GRE_VERBAL": 158,
    "MBA_GRE_QUANT": 160,
    "MBA_NATIVE_ENGLISH": False,
    "MBA_IELTS": {
        "listening": 8.0,
        "reading": 8.0,
        "writing": 8.0,
        "speaking": 8.0,
    },
    "MBA_DOCUMENTS": {
        "resume": True,
        "essay_1": True,
        "essay_2": True,
        "reference_1": True,
        "reference_2": True,
        "transcripts": True,
    },
}

SCENARIOS: Dict[str, Scenario] = {"real": REAL, "ideal": IDEAL}


def _apply(profile: str) -> None:
    if profile not in SCENARIOS:
        raise ValueError(f"PROFILE must be one of {tuple(SCENARIOS)}, got {profile!r}")
    globals().update(SCENARIOS[profile])


_apply(PROFILE)

__all__ = [
    "PROFILE",
    "SCENARIOS",
    "AGE",
    "EDUCATION",
    "FOREIGN_WORK_YEARS",
    "IELTS",
    "TCF",
    "ENGLISH_EXAM_DONE",
    "FRENCH_EXAM_DONE",
    "PROOF_OF_FUNDS_CAD",
    "PROOF_OF_WORK",
    "ECA_DONE",
    "POLICE_CERTIFICATES_DONE",
    "PASSPORT_VALID",
    "PNP",
    "CANADIAN_EDUCATION",
    "RELATIVE_IN_CANADA",
    "JOB_OFFER",
    "MBA_APPLICANT_TYPE",
    "MBA_INTAKE",
    "MBA_INTAKE_YEAR",
    "MBA_GPA_LAST_TWO_YEARS",
    "MBA_HAS_FOUR_YEAR_DEGREE",
    "MBA_WORK_YEARS",
    "MBA_GMAT_SCORE",
    "MBA_GRE_VERBAL",
    "MBA_GRE_QUANT",
    "MBA_NATIVE_ENGLISH",
    "MBA_IELTS",
    "MBA_DOCUMENTS",
]
