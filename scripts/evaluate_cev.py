"""CEV/SpACER diagnostic separating OCR and parsing on three NewsEye pages.

Character positions are unavailable. Parsing-only text is approximated by each
reference word centre falling inside predicted line polygons; duplicated coverage
duplicates its characters. This is a triage diagnostic, not exact CEV ground truth.
"""
from pathlib import Path
from collections import Counter
import json
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cv2
import numpy as np
from lxml import etree as E

from bbvlm.metrics import spacer
from bbvlm.pero import load_cache

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/cev-v1"
OUT.mkdir(parents=True, exist_ok=True)


def profile(text):
    text = unicodedata.normalize("NFC", text).replace("ſ", "s").casefold()
    return "".join(c for c in text if not c.isspace())


def reference_words(xml):
    tree = E.parse(str(xml))
    rows = []
    for word in tree.findall(".//{*}Word"):
        pts = np.array([list(map(float, p.split(","))) for p in word.find("{*}Coords").get("points").split()])
        rows.append({"text": word.findtext("{*}TextEquiv/{*}Unicode", default=""),
                     "centre": pts.mean(0).tolist()})
    return rows


def predicted(layout_xml):
    tree = E.parse(str(layout_xml))
    lines = []
    for line in tree.findall(".//{*}TextLine"):
        pts = np.array([list(map(float, p.split(","))) for p in line.find("{*}Coords").get("points").split()], np.float32)
        text = line.findtext("{*}TextEquiv/{*}Unicode", default="")
        lines.append({"polygon": pts, "text": text})
    return lines


results = []
for page_id in ["0253902-001", "0401692-003", "752234-003"]:
    source = json.loads((ROOT / "experiments/loop/cache" / page_id / "run.json").read_text())
    words = reference_words(ROOT / source["source_xml"])
    q = profile(" ".join(w["text"] for w in words))
    oracle_layout, _ = load_cache(ROOT / "experiments/loop/cache" / page_id)
    s_star = profile(" ".join(line.transcription or "" for line in oracle_layout.lines_iterator()))
    lines = predicted(ROOT / "experiments/loop/end-to-end" / page_id / "layout.xml")
    s = profile(" ".join(line["text"] for line in lines))
    parsed_reference = []
    missed = duplicated = 0
    for word in words:
        hits = sum(cv2.pointPolygonTest(line["polygon"], tuple(word["centre"]), False) >= 0 for line in lines)
        if hits == 0:
            missed += 1
        if hits > 1:
            duplicated += 1
        parsed_reference.extend([word["text"]] * hits)
    r = profile(" ".join(parsed_reference))
    result = {
        "page": page_id,
        "reference_words": len(words),
        "reference_words_missed_by_predicted_line_polygons": missed,
        "reference_words_covered_more_than_once": duplicated,
        "characters": {"Q_reference": len(q), "R_parsing_only": len(r),
                       "S_star_ocr_on_reference_lines": len(s_star), "S_end_to_end": len(s)},
        "spacer": {
            "ocr_only_d_Sstar_Q": spacer(q, s_star),
            "parsing_only_d_R_Q": spacer(q, r),
            "interaction_d_S_R": spacer(r, s),
            "total_d_S_Q": spacer(q, s),
        },
        "approximation": "reference word centre inside predicted line polygon; no character positions",
        "reference_warning": "distributed NewsEye text contains audited corruption; values are diagnostic only",
        "normalization": "NFC, long-s fold, casefold, whitespace removed; punctuation retained",
    }
    results.append(result)

report = {"schema": "bbvlm.cev-diagnostic/1", "method": "SpACER; arXiv:2604.06160",
          "results": results, "certified_ground_truth": False}
(OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(results, ensure_ascii=False, indent=2))
