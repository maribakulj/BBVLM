"""Evaluation with explicit denominators, including missing outputs."""
import unicodedata
from collections import Counter
from .document import index


def edit_distance(a, b):
    row = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        nxt = [i]
        for j, cb in enumerate(b, 1):
            nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(ca != cb)))
        row = nxt
    return row[-1]


def normalise(text):
    """Only NFC + long-s fold. Does not repair spelling, spaces or punctuation."""
    return unicodedata.normalize("NFC", text).replace("ſ", "s")


def spacer(reference, hypothesis):
    """Spatially Aware Character Error Rate from character-count vectors.

    Callers decide the normalization and spatial aggregation. This function
    intentionally does not reorder, lowercase, or discard punctuation.
    Formula follows Bourne, Simbeye & Nockels (2026), arXiv:2604.06160.
    """
    if not isinstance(reference, str) or not isinstance(hypothesis, str):
        raise TypeError("SpACER inputs must be strings")
    if not reference:
        return None
    left, right = Counter(reference), Counter(hypothesis)
    l1 = sum(abs(left[c] - right[c]) for c in left.keys() | right.keys())
    deletions = max(0, len(reference) - len(hypothesis))
    return (deletions + l1) / (2 * len(reference))


def text_scores(reference, hypothesis):
    """Reference/hypothesis: lists of {id,text}; duplicate IDs are errors."""
    ref = {r["id"]: r["text"] for r in reference}
    hyp = {r["id"]: r["text"] for r in hypothesis}
    if len(ref) != len(reference) or len(hyp) != len(hypothesis):
        raise ValueError("duplicate line IDs in evaluation")
    unknown = set(hyp)-set(ref)
    if unknown:
        raise ValueError(f"unknown hypothesis IDs: {sorted(unknown)}")
    rows = []
    for lid, text in ref.items():
        out = hyp.get(lid, "")
        rows.append({"id": lid, "reference": text, "hypothesis": out,
                     "characters": len(text), "edits": edit_distance(text, out),
                     "normalised_characters": len(normalise(text)),
                     "normalised_edits": edit_distance(normalise(text), normalise(out)),
                     "missing": lid not in hyp, "exact": text == out})
    chars = sum(r["characters"] for r in rows)
    norm_chars = sum(r["normalised_characters"] for r in rows)
    return {"lines": len(rows), "missing_lines": sum(r["missing"] for r in rows),
            "exact_lines": sum(r["exact"] for r in rows), "characters": chars,
            "edits": sum(r["edits"] for r in rows),
            "cer": sum(r["edits"] for r in rows)/chars if chars else None,
            "cer_nfc_long_s": sum(r["normalised_edits"] for r in rows)/norm_chars if norm_chars else None,
            "normalisation": "NFC and ſ→s only", "per_line": rows}


def iou(a, b):
    area = max(0, min(a[2], b[2])-max(a[0], b[0]))*max(0, min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-area
    return area/union if union else 0.


def word_scores(reference, hypothesis, threshold=0.5):
    """Maximum-cardinality matching: exact diplomatic text AND IoU >= threshold.

    Assumes explicitly corresponding page IDs and equal pixel dimensions.
    Missing word boxes count as misses; this metric cannot certify line-only GT.
    """
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    if not 0 < threshold <= 1:
        raise ValueError("IoU threshold must be in (0,1]")
    rp = {n["id"]: n for n in reference["nodes"] if n["kind"] == "page"}
    hp = {n["id"]: n for n in hypothesis["nodes"] if n["kind"] == "page"}
    if set(rp) != set(hp) or any(rp[k]["bbox"] != hp[k]["bbox"] for k in rp):
        raise ValueError("page IDs/dimensions must correspond explicitly")
    rw = [n for n in reference["nodes"] if n["kind"] == "word"]
    hw = [n for n in hypothesis["nodes"] if n["kind"] == "word"]
    if not rw:
        raise ValueError("reference has no word geometry; do not score it as perfect")
    matches = 0
    for pid in rp:
        a = [n for n in rw if n["page"] == pid]
        b = [n for n in hw if n["page"] == pid]
        if not a or not b:
            continue
        matrix = np.array([[float(x["text"] == y["text"] and iou(x["bbox"], y["bbox"]) >= threshold)
                            for y in b] for x in a])
        ii, jj = linear_sum_assignment(-matrix)
        matches += int(matrix[ii, jj].sum())
    p = matches/len(hw) if hw else 0.
    r = matches/len(rw)
    return {"reference_words": len(rw), "predicted_words": len(hw), "matched_words": matches,
            "precision": p, "recall": r, "f1": 2*p*r/(p+r) if p+r else 0.,
            "iou_threshold": threshold, "text": "exact, no normalisation",
            "reference_lines_without_words": sum(n["kind"] == "line" and not any(
                w["parent"] == n["id"] for w in rw) for n in reference["nodes"])}
