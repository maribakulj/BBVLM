#!/usr/bin/env python3
"""Seal opaque image-plus-PERO inputs for the one-pass A54 Luna reader."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/bnl-independent-a54"


def main() -> None:
    split = json.loads((EXP / "split.json").read_text())
    predictions = json.loads((EXP / "output/predictions.json").read_text())
    by_id = {row["id"]: row for row in predictions["blocks"]}
    ids = split["selection"]["ids"]
    if set(ids) != set(by_id):
        raise ValueError("prediction and frozen split IDs differ")
    ordered = sorted(ids, key=lambda value: hashlib.sha256(("BBVLM-A54-request:" + value).encode()).hexdigest())
    mapping = {f"T{index:03d}": identifier for index, identifier in enumerate(ordered, 1)}
    items = []
    for opaque, identifier in mapping.items():
        candidate = "\n".join(line["text"] for line in by_id[identifier]["lines"])
        items.append({
            "id": opaque,
            "image": str((EXP / "source" / f"{identifier}.png").resolve()),
            "pero_candidate": candidate,
            "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
        })
    request = {
        "schema": "bbvlm.blind-image-candidate-request/1",
        "task": "For every image, return the visible transcription. The PERO candidate is independent evidence, not truth. Preserve it exactly when the pixels do not justify a change. Make only localized visually justified changes; do not modernize spelling, expand abbreviations, or silently normalize punctuation. Preserve visible line breaks when practical. If a glyph is genuinely unreadable, retain the candidate glyph and mark uncertain rather than guessing.",
        "output_schema": {
            "items": [{"id": "T001", "text": "transcription", "decision": "keep|edit", "uncertain": False,
                       "edits": [{"before": "exact candidate substring", "after": "replacement", "visual_reason": "brief pixel evidence"}]}],
            "inspected_images": ["absolute paths actually inspected"]
        },
        "constraints": [
            "Return exactly one item for every unique request ID and no additional IDs.",
            "Actually inspect every image at readable resolution.",
            "Do not inspect XML, references, scores, other experiments, Git history, or other agents.",
            "Every edit must identify an exact candidate substring; keep is preferred to an ungrounded rewrite.",
            "The output must be valid JSON without Markdown fences."
        ],
        "items": items,
    }
    input_dir = EXP / "vlm-input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n")
    (input_dir / "private-map.json").write_text(json.dumps({"schema": "bbvlm.private-id-map/1", "mapping": mapping}, indent=2) + "\n")
    print(json.dumps({"items": len(items), "request": str(input_dir / "request.json")}, indent=2))


if __name__ == "__main__":
    main()
