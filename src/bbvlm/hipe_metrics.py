"""HIPE-OCRepair 0.9.9 compatible normalization and MER counts.

The normalization is transcribed from the upstream scorer at commit
d1e76e447629ea9cf8dead32ae3c44b0d48d77b3.  The alignment implementation is
dependency-free and regression-tested against jiwer.process_characters.
"""
from __future__ import annotations

import re


UPSTREAM_REVISION = "d1e76e447629ea9cf8dead32ae3c44b0d48d77b3"


def hipe_normalize(string: str) -> str:
    """Apply the scorer's exact ordered text substitutions."""
    string = string.lower()
    for before, after in (
        ("ß", "ss"), ("ꝛ", "r"), ("œ", "oe"), ("æ", "ae"),
        ("aͤ", "ä"), ("oͤ", "ö"), ("uͤ", "ü"),
    ):
        string = string.replace(before, after)
    string = string.replace("—\n", "").replace("¬\n", "")
    string = re.sub(r"[^\w]", " ", string, flags=re.UNICODE)
    string = string.replace("_", " ")
    return re.sub(r"\s+", " ", string).strip()


def alignment_counts(reference: str, hypothesis: str) -> dict[str, int]:
    """Return jiwer-compatible H/S/D/I counts for characters.

    Dynamic-programming cells minimize edit cost. On equal costs we prefer a
    diagonal operation, then deletion, then insertion, matching RapidFuzz's
    opcode counts on the upstream scorer's use cases and the regression suite.
    """
    rows, columns = len(reference) + 1, len(hypothesis) + 1
    cost = [[0] * columns for _ in range(rows)]
    back = [[None] * columns for _ in range(rows)]
    for i in range(1, rows):
        cost[i][0], back[i][0] = i, "delete"
    for j in range(1, columns):
        cost[0][j], back[0][j] = j, "insert"
    priority = {"equal": 0, "substitute": 0, "delete": 1, "insert": 2}
    for i in range(1, rows):
        for j in range(1, columns):
            diagonal = "equal" if reference[i - 1] == hypothesis[j - 1] else "substitute"
            choices = (
                (cost[i - 1][j - 1] + (diagonal != "equal"), diagonal),
                (cost[i - 1][j] + 1, "delete"),
                (cost[i][j - 1] + 1, "insert"),
            )
            cost[i][j], back[i][j] = min(choices, key=lambda item: (item[0], priority[item[1]]))
    counts = {"hits": 0, "substitutions": 0, "deletions": 0, "insertions": 0}
    i, j = len(reference), len(hypothesis)
    while i or j:
        operation = back[i][j]
        if operation == "equal":
            counts["hits"] += 1; i -= 1; j -= 1
        elif operation == "substitute":
            counts["substitutions"] += 1; i -= 1; j -= 1
        elif operation == "delete":
            counts["deletions"] += 1; i -= 1
        elif operation == "insert":
            counts["insertions"] += 1; j -= 1
        else:
            raise AssertionError("invalid alignment backtrace")
    return counts


def cmer(reference: str, hypothesis: str) -> dict[str, object]:
    """Normalize, align and compute character Match Error Rate."""
    left, right = hipe_normalize(reference), hipe_normalize(hypothesis)
    counts = alignment_counts(left, right)
    errors = counts["substitutions"] + counts["deletions"] + counts["insertions"]
    denominator = counts["hits"] + errors
    return {"reference": left, "hypothesis": right, **counts,
            "errors": errors, "denominator": denominator,
            "cmer": errors / denominator if denominator else 0.0,
            "exact": left == right}
