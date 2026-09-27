"""Deterministic integrity audit of the distributed NewsEye validation PAGE XML.

This checks internal consistency and Unicode hygiene only. It cannot verify the
text against pixels and deliberately does not rewrite any source annotation.
"""
from pathlib import Path
from collections import Counter
import json
import unicodedata

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpora/newseye-validation"
OUT = ROOT / "experiments/loop/reference-audit-v1/structural-audit.json"

pages = []
global_chars = Counter()


def propose_utf8_latin1_repair(text):
    """Decode only locally valid UTF-8 byte runs misread as Latin-1.

    This is evidence for an encoding defect, not an automatic source rewrite.
    """
    out = []
    repairs = []
    i = 0
    while i < len(text):
        found = None
        for width in (4, 3, 2):
            chunk = text[i:i + width]
            try:
                raw = chunk.encode("latin-1")
                decoded = raw.decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if len(decoded) == 1 and ord(decoded) >= 128:
                found = (width, decoded)
                break
        if found:
            width, decoded = found
            repairs.append({"offset": i, "before": text[i:i + width], "after": decoded,
                            "after_codepoint": f"U+{ord(decoded):04X}"})
            out.append(decoded)
            i += width
        else:
            out.append(text[i])
            i += 1
    return "".join(out), repairs


for xml_path in sorted(CORPUS.rglob("*.xml")):
    tree = E.parse(str(xml_path))
    lines = tree.findall(".//{*}TextLine")
    words = tree.findall(".//{*}Word")
    line_word_mismatches = []
    empty_lines = []
    controls = []
    non_nfc = []
    encoding_repair_candidates = []
    for line in lines:
        text = line.findtext("{*}TextEquiv/{*}Unicode", default="")
        for char in text:
            global_chars[char] += 1
            category = unicodedata.category(char)
            if category.startswith("C") and char not in "\n\t":
                controls.append({"line": line.get("id"), "codepoint": f"U+{ord(char):04X}",
                                 "name": unicodedata.name(char, "UNNAMED")})
        if unicodedata.normalize("NFC", text) != text:
            non_nfc.append(line.get("id"))
        repaired, repairs = propose_utf8_latin1_repair(text)
        if repairs:
            encoding_repair_candidates.append({"line": line.get("id"), "original": text,
                                               "proposal": repaired, "repairs": repairs})
        if not text.strip():
            empty_lines.append(line.get("id"))
        line_words = line.findall("{*}Word")
        if line_words:
            joined = " ".join(w.findtext("{*}TextEquiv/{*}Unicode", default="") for w in line_words)
            if joined != text:
                line_word_mismatches.append({"line": line.get("id"), "line_text": text,
                                             "joined_word_text": joined})
    pages.append({
        "page": xml_path.stem,
        "xml": str(xml_path.relative_to(ROOT)),
        "lines": len(lines),
        "words": len(words),
        "lines_with_words": sum(bool(line.findall("{*}Word")) for line in lines),
        "empty_line_texts": empty_lines,
        "line_word_text_mismatches": line_word_mismatches,
        "non_nfc_line_ids": non_nfc,
        "control_or_format_characters": controls,
        "encoding_repair_candidates": encoding_repair_candidates,
    })

report = {
    "schema": "bbvlm.reference-structural-audit/1",
    "scope": "internal XML consistency and Unicode hygiene; not visual truth",
    "pages": pages,
    "totals": {
        "pages": len(pages),
        "lines": sum(p["lines"] for p in pages),
        "words": sum(p["words"] for p in pages),
        "empty_line_texts": sum(len(p["empty_line_texts"]) for p in pages),
        "line_word_text_mismatches": sum(len(p["line_word_text_mismatches"]) for p in pages),
        "non_nfc_lines": sum(len(p["non_nfc_line_ids"]) for p in pages),
        "control_or_format_characters": sum(len(p["control_or_format_characters"]) for p in pages),
        "lines_with_recoverable_utf8_latin1_sequences": sum(len(p["encoding_repair_candidates"]) for p in pages),
    },
    "unusual_characters": [
        {"char": c, "codepoint": f"U+{ord(c):04X}", "name": unicodedata.name(c, "UNNAMED"), "count": n}
        for c, n in sorted(global_chars.items(), key=lambda item: ord(item[0]))
        if ord(c) < 32 or ord(c) > 126
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report["totals"], indent=2))
