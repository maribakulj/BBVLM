"""Compare a blind reader, distributed PAGE text, and PERO on a fixed sample.

Agreement is a triage signal, never an adjudication. The script exposes strict,
typographic, and IR-oriented profiles separately and keeps every sampled line.
"""
from pathlib import Path
import json
import math
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bbvlm.metrics import edit_distance
from bbvlm.pero import load_cache

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/reference-audit-v1"


def typographic(text):
    table = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "‐": "-", "‑": "-",
                           "‒": "-", "–": "-", "—": "-", "−": "-", "ſ": "s"})
    return unicodedata.normalize("NFC", text).translate(table)


def ir(text):
    # HIPE-inspired retrieval view. Does not replace the diplomatic layer.
    text = typographic(text).lower()
    text = "".join(c if c.isalnum() or c == "_" else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()


def aggregate(a, b, normalizer):
    chars = edits = exact = 0
    rows = []
    for lid in a:
        left, right = normalizer(a[lid]), normalizer(b[lid])
        distance = edit_distance(left, right)
        chars += len(left)
        edits += distance
        exact += left == right
        rows.append({"id": lid, "left": left, "right": right, "edits": distance,
                     "characters": len(left), "rate": distance / max(1, len(left))})
    return {"lines": len(a), "exact_lines": exact, "characters": chars,
            "edits": edits, "cer": edits / max(1, chars), "per_line": rows}


def wilson(successes, total, z=1.96):
    if not total:
        return None
    p = successes / total
    den = 1 + z*z/total
    centre = (p + z*z/(2*total))/den
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total))/den
    return [centre-half, centre+half]


request = json.loads((BASE / "input/request.json").read_text())
reference_rows = json.loads((BASE / "evaluation/distributed-reference.json").read_text())
response = json.loads((BASE / "luna.response.json").read_text())
expected = request["requested_line_ids"]
if response.get("requested_line_ids") != expected:
    raise ValueError("reader echoed a changed request or order")
if len(response.get("lines", [])) != len(expected):
    raise ValueError("reader omitted or added lines")
reader = {r["id"]: r["text"] for r in response["lines"]}
if set(reader) != set(expected) or len(reader) != len(response["lines"]):
    raise ValueError("reader IDs differ or repeat")
distributed = {r["id"]: r["distributed_text"] for r in reference_rows}

pero = {}
by_page = {}
for row in reference_rows:
    by_page.setdefault(row["page"], []).append(row)
for page_id, rows in by_page.items():
    layout, _ = load_cache(ROOT / "experiments/loop/cache" / page_id)
    lines = {line.id: line.transcription or "" for line in layout.lines_iterator()}
    for row in rows:
        pero[row["id"]] = lines.get(row["source_line_id"], "")

comparisons = {}
for profile, normalizer in [("strict", lambda x: x), ("typographic", typographic), ("ir", ir)]:
    comparisons[profile] = {
        "distributed_vs_luna": aggregate(distributed, reader, normalizer),
        "distributed_vs_pero": aggregate(distributed, pero, normalizer),
        "luna_vs_pero": aggregate(reader, pero, normalizer),
    }

triage = []
categories = {}
for row in reference_rows:
    lid = row["id"]
    g, l, p = map(typographic, [distributed[lid], reader[lid], pero[lid]])
    if g == l == p:
        category = "all_agree"
    elif l == p and g != l:
        category = "luna_pero_agree_against_distributed"
    elif g == l and p != g:
        category = "distributed_luna_agree_against_pero"
    elif g == p and l != g:
        category = "distributed_pero_agree_against_luna"
    else:
        dl, dp, lp = edit_distance(g, l), edit_distance(g, p), edit_distance(l, p)
        if lp < min(dl, dp):
            category = "luna_pero_closer_than_distributed"
        else:
            category = "all_disagree_or_no_clear_pair"
    categories[category] = categories.get(category, 0) + 1
    triage.append({"id": lid, "page": row["page"], "source_line_id": row["source_line_id"],
                   "category": category, "distributed": distributed[lid], "luna": reader[lid],
                   "pero": pero[lid], "luna_uncertain": next(x for x in response["lines"] if x["id"] == lid)["uncertain"],
                   "notes": next(x for x in response["lines"] if x["id"] == lid)["notes"]})

suspect = categories.get("luna_pero_agree_against_distributed", 0) + categories.get("luna_pero_closer_than_distributed", 0)
report = {
    "schema": "bbvlm.reference-audit/1",
    "sample": request["selection"],
    "sample_size": len(expected),
    "reader": "gpt-6-luna; one blind pass; no reference or PERO text exposed",
    "profiles": {
        "strict": "NFC-unmodified diplomatic strings",
        "typographic": "NFC; apostrophe/dash families folded; long s→s",
        "ir": "typographic profile; lowercase; punctuation→space; whitespace collapsed",
    },
    "comparisons": comparisons,
    "triage_categories": categories,
    "triage_signal_lines": suspect,
    "triage_signal_rate": suspect / len(expected),
    "triage_signal_wilson95": wilson(suspect, len(expected)),
    "uncertain_reader_lines": sum(bool(r["uncertain"]) for r in response["lines"]),
    "interpretation": "Pairwise agreement only prioritizes independent human review; it cannot decide which text is true.",
    "lines": triage,
}
(BASE / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k not in {"comparisons", "lines"}}, ensure_ascii=False, indent=2))
for profile, values in comparisons.items():
    print(profile, {k: {"cer": round(v["cer"], 5), "exact": v["exact_lines"]} for k, v in values.items()})
