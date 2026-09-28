#!/usr/bin/env python3
"""Score A52 without mixing OCR accuracy and reading order."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from bbvlm.ocr_conventions import transform
from bbvlm.text_views import retrieval_fold_v1


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/crossbranch-ocr-a52"
TIRETS = str.maketrans({c: "-" for c in "‐‑‒–—⸗\u00ad"})
APOS = str.maketrans({c: "'" for c in "’ʼ‘"})
E_ABOVE = {"a\u0364": "ä", "o\u0364": "ö", "u\u0364": "ü"}


def normalise(text: str, profile: str) -> str:
    text = unicodedata.normalize("NFC", text)
    if profile == "strict":
        return text
    text = transform(text, "glyph_decomposition_v1")
    if profile == "diplomatic":
        return text
    if profile == "retrieval_fold_v1":
        return retrieval_fold_v1(text)
    if profile != "search_v1":
        raise ValueError(profile)
    text = text.replace("ſ", "s").translate(TIRETS).translate(APOS)
    for source, target in E_ABOVE.items():
        text = text.replace(source, target)
    # Gallica/Exalead-like retrieval view: line-end hyphenation, punctuation,
    # whitespace and case do not count; letters and diacritics still do.
    text = text.casefold().replace("-", "")
    return "".join(c for c in text if unicodedata.category(c)[0] in {"L", "N", "M"})


def lev(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def score(reference: list[str], hypothesis: list[str], profile: str) -> dict:
    refs = [normalise(x, profile) for x in reference if x.strip()]
    hyps = [normalise(x, profile) for x in hypothesis if x.strip()]
    denom = sum(map(len, refs))
    costs = np.array([[lev(r, h) for h in hyps] for r in refs], dtype=float)
    if not hyps:
        rows, cols = np.array([], dtype=int), np.array([], dtype=int)
    else:
        rows, cols = linear_sum_assignment(costs)
    pairs, used_r, used_h, edits = [], set(), set(), 0
    for ri, hi in zip(rows, cols):
        ed = int(costs[ri, hi])
        if ed > len(refs[ri]):
            continue
        pairs.append({"ref_index": int(ri), "hyp_index": int(hi), "ref": refs[ri], "hyp": hyps[hi], "edits": ed})
        used_r.add(int(ri)); used_h.add(int(hi)); edits += ed
    for ri, ref in enumerate(refs):
        if ri not in used_r:
            pairs.append({"ref_index": ri, "hyp_index": None, "ref": ref, "hyp": None, "edits": len(ref)})
            edits += len(ref)
    for hi, hyp in enumerate(hyps):
        if hi not in used_h:
            pairs.append({"ref_index": None, "hyp_index": hi, "ref": None, "hyp": hyp, "edits": len(hyp)})
            edits += len(hyp)
    return {
        "profile": profile,
        "reference_characters": denom,
        "edits": edits,
        "cer": edits / denom if denom else None,
        "exact_lines": sum(p["edits"] == 0 for p in pairs),
        "reference_lines": len(refs),
        "hypothesis_lines": len(hyps),
        "errors": [p for p in pairs if p["edits"]],
    }


def lines(text: str) -> list[str]:
    return [x.rstrip() for x in re.split(r"\r?\n", text.strip()) if x.strip()]


def main() -> None:
    imported = json.loads((BASE / "claude-o02-import.json").read_text(encoding="utf-8"))
    luna = json.loads((BASE / "luna-output.json").read_text(encoding="utf-8"))
    luna_pages = {page["id"]: lines(page["text"]) for page in luna["pages"]}
    sol_path = BASE / "sol-output.json"
    sol = json.loads(sol_path.read_text(encoding="utf-8")) if sol_path.exists() else None
    escalated: dict[str, list[str]] = {}
    if sol:
        p01 = list(luna_pages["A52-P01"])
        prefixes = ("tunés, qui", "à ", "bien les lumi")
        for prefix, replacement in zip(prefixes, sol["p01_lines"]):
            candidates = [i for i, value in enumerate(p01) if value.startswith(prefix)]
            if len(candidates) != 1:
                raise ValueError(f"cannot apply targeted P01 replacement {prefix!r}: {candidates}")
            p01[candidates[0]] = replacement
        escalated = {"A52-P01": p01, "A52-P02": lines(sol["p02_text"])}
    report = {
        "schema": "bbvlm.a52-report/1",
        "experiment_class": "development_cross_branch_replication",
        "independent": False,
        "passes": {"luna": 1, "sol_targeted_after_failure": int(bool(sol))},
        "profiles": {
            "strict": "NFC exact Unicode",
            "diplomatic": "documented OCR-D/GT4HistOCR PUA ligature decomposition; long s, punctuation and e-above preserved",
            "search_v1": "diplomatic + casefold + long-s folding + superscript-e/umlaut equivalence + punctuation/space/hyphen deletion",
            "retrieval_fold_v1": "accent-insensitive alphanumeric key used only for retrieval/equivalence, never diplomatic truth",
        },
        "pages": {},
    }
    for page_id, data in imported["pages"].items():
        report["pages"][page_id] = {}
        readers = [("luna", luna_pages[page_id]), ("opus_o02_A1", data["opus"])]
        if "opus_alt" in data:
            readers.append(("opus_o02_A2", data["opus_alt"]))
        if sol:
            readers.append(("luna_plus_targeted_sol", escalated[page_id]))
        for reader, hyp in readers:
            report["pages"][page_id][reader] = {}
            for ref_name in ("distributed", "adjudicated"):
                report["pages"][page_id][reader][ref_name] = {
                    p: score(data[ref_name], hyp, p)
                    for p in ("strict", "diplomatic", "search_v1", "retrieval_fold_v1")
                }
    (BASE / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for pid, readers in report["pages"].items():
        print(pid)
        for reader, refs in readers.items():
            vals = refs["adjudicated"]
            print(reader, *(f"{p}={100*vals[p]['cer']:.3f}%({vals[p]['edits']})" for p in vals))


if __name__ == "__main__":
    main()
