"""
Shared language helper functions reused across scripts.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from conversion_tables import IELTS_CLB_TABLE, TCF_NCLC_TABLE

# French NCLC thresholds relevant for actionable targets.
FRENCH_THRESHOLDS = (5, 7, 9)


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


__all__ = [
    "FRENCH_THRESHOLDS",
    "zero_clb",
    "ielts_to_clb",
    "tcf_to_nclc",
    "clb_stats",
    "next_clb_target",
    "next_relevant_french_target",
]

