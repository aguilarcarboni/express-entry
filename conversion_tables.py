"""
Language score conversion tables kept separate for reuse and clarity.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

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

__all__ = ["IELTS_CLB_TABLE", "TCF_NCLC_TABLE"]

