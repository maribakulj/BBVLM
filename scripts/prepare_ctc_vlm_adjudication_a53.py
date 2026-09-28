#!/usr/bin/env python3
"""Prepare A53: one visually grounded adjudication pass over VLM/CTC disagreements.

The public task contains only source crops and randomly labelled candidates.  The
reference, candidate provenance and CTC path costs are written separately and
must not be exposed to the reader before its response is frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np


SEED = 2026092801


def _alto_lines(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.glob("native-*.alto.xml")):
        tree = ET.parse(path)
        for line in tree.getroot().iter():
            if not line.tag.endswith("TextLine"):
                continue
            words = [node.get("CONTENT", "") for node in line if node.tag.endswith("String")]
            out[line.get("ID", "")] = " ".join(words)
    return out


def _log_softmax(x: np.ndarray) -> np.ndarray:
    maximum = x.max(axis=1, keepdims=True)
    shifted = x - maximum
    return shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))


def _ctc_viterbi_cost(logits: np.ndarray, text: str, characters: list[str], coords: list[int]) -> float | None:
    blank = logits.shape[1] - 1
    codec = {character: index for index, character in enumerate(characters)}
    if not text or any(character not in codec or codec[character] >= blank for character in text):
        return None
    codes = [codec[character] for character in text]
    states = [blank]
    for code in codes:
        states.extend((code, blank))
    logp = _log_softmax(logits[int(coords[0]):int(coords[1])])
    frames, state_count = logp.shape[0], len(states)
    if frames < len(codes):
        return None
    neg = -1e100
    previous = np.full(state_count, neg, dtype=np.float64)
    previous[0] = logp[0, states[0]]
    if state_count > 1:
        previous[1] = logp[0, states[1]]
    for frame in range(1, frames):
        current = np.full(state_count, neg, dtype=np.float64)
        for state in range(state_count):
            best = previous[state]
            if state >= 1:
                best = max(best, previous[state - 1])
            if state >= 2 and states[state] != blank and states[state] != states[state - 2]:
                best = max(best, previous[state - 2])
            if best > neg / 2:
                current[state] = best + logp[frame, states[state]]
        previous = current
    score = max(previous[-1], previous[-2] if state_count > 1 else neg)
    if not math.isfinite(float(score)):
        return None
    return float(-score / frames)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("experiments/loop"))
    args = parser.parse_args()
    loop = args.root
    a23 = loop / "ctc-fallback-a23"
    out = loop / "ctc-vlm-adjudication-a53"
    out.mkdir(parents=True, exist_ok=True)

    vlm = json.loads((a23 / "final-transcriptions.json").read_text(encoding="utf-8"))
    native = _alto_lines(a23)
    refs = {item["id"]: item["text"] for item in json.loads(
        (loop / "reserve-a22" / "private-reference.json").read_text(encoding="utf-8")
    )}
    if set(vlm) != set(native) or not set(vlm) <= set(refs):
        raise ValueError("A23 candidate/reference identity mismatch")

    cache_index: dict[str, tuple[np.ndarray, list[str], list[int]]] = {}
    for cache_dir in sorted((a23 / "recognition").iterdir()):
        if not cache_dir.is_dir():
            continue
        meta = json.loads((cache_dir / "cache.json").read_text(encoding="utf-8"))
        with np.load(cache_dir / "logits.npz", allow_pickle=False) as arrays:
            for item in meta["lines"]:
                cache_index[item["id"]] = (
                    arrays[item["key"]].copy(), item["characters"], item["logit_coords"]
                )

    rng = random.Random(SEED)
    public_items, private_items = [], []
    for line_id in sorted(vlm):
        if unicodedata.normalize("NFC", vlm[line_id]) == unicodedata.normalize("NFC", native[line_id]):
            continue
        options = [("vlm", vlm[line_id]), ("ctc", native[line_id])]
        rng.shuffle(options)
        labelled = {"A": options[0][1], "B": options[1][1]}
        provenance = {"A": options[0][0], "B": options[1][0]}
        image = loop / "vlm-input-a24" / "input" / f"{line_id}.png"
        if not image.exists():
            raise FileNotFoundError(image)
        logits, characters, coords = cache_index[line_id]
        costs = {label: _ctc_viterbi_cost(logits, text, characters, coords)
                 for label, text in labelled.items()}
        public_items.append({
            "id": line_id,
            "image": str(image),
            "option_A": labelled["A"],
            "option_B": labelled["B"],
        })
        private_items.append({
            "id": line_id,
            "reference": refs[line_id],
            "options": labelled,
            "provenance": provenance,
            "ctc_viterbi_nll_per_frame": costs,
        })

    public = {
        "schema": "bbvlm.ctc-vlm-adjudication-task/1",
        "seed": SEED,
        "instructions": (
            "Inspect every image at high/original resolution. Choose A or B only when it exactly "
            "matches the visible print. If both differ, return NEITHER plus an exact diplomatic "
            "transcription. Preserve long-s, diacritics, punctuation, abbreviations and historical spelling."
        ),
        "items": public_items,
    }
    private = {
        "schema": "bbvlm.ctc-vlm-adjudication-private/1",
        "source_scope": "Consumed A23 lines; development diagnostic only",
        "reader_must_not_receive_this_file": True,
        "items": private_items,
    }
    (out / "public-task.json").write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "private-evaluation.json").write_text(json.dumps(private, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256((out / "public-task.json").read_bytes()).hexdigest()
    print(json.dumps({"items": len(public_items), "public_sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
