#!/usr/bin/env python3
"""Freeze unopened Finlam pages for semantic-boundary validation after A50."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-boundaries-a51"
DECLARED_ROWS = 433
SEED = "bbvlm-finlam-a51-semantic-boundaries-2026-09-28-v1"

# A48/A49 rows plus every row whose viewer metadata/content was inspected in
# the A50 adjacent-page diagnosis.  None can be called independent again.
EXCLUDED = set(range(82, 103)) | set(range(125, 146)) | set(range(176, 197))
EXCLUDED |= set(range(346, 367)) | set(range(399, 430))
EXCLUDED |= {73, 242, 365}


def rank(index: int) -> str:
    return hashlib.sha256(f"{SEED}:{index}".encode()).hexdigest()


def main() -> None:
    EXP.mkdir(parents=True, exist_ok=True)
    candidates = [index for index in range(DECLARED_ROWS) if index not in EXCLUDED]
    selected = sorted(candidates, key=rank)[:8]
    split = {
        "schema": "bbvlm.finlam-boundaries-a51-split/1",
        "status": "frozen before row content or images are opened",
        "source": {
            "dataset": "Teklia/Newspapers-finlam-La-Liberte",
            "revision": "c3d69ca1eef5a0f479b6aeaa6d6c155b3ec93657",
            "config": "default", "split": "test", "declared_rows": DECLARED_ROWS,
        },
        "selection": {
            "method": "lowest SHA-256 ranks over eligible row indices",
            "seed": SEED, "row_indices": selected,
            "content_seen_before_freeze": False,
            "excluded_rows_or_windows": sorted(EXCLUDED),
        },
        "frozen_system": {
            "geometry": "infer_recurrent_column_order A49 parameters unchanged",
            "cheap_title_boundary": "run of TITLE zones opens one article",
            "semantic_router": {"gap_fraction_gt": 0.004,
                                "horizontal_overlap_fraction_lt": 0.25},
            "vlm_prompt": "A50 request rules and labels unchanged; one Luna pass per page packet; unclear means conservative continuation",
            "vlm_scope": "routed article boundaries plus evidence-bound metadata/semantic enrichment; never physical column order",
        },
        "gates": {
            "macro_article_same_pair_f1_min": 0.80,
            "macro_global_pair_accuracy_min": 0.90,
            "macro_within_article_micro_accuracy_min": 0.98,
            "candidate_article_f1_strictly_above_title_cut": True,
            "no_page_article_f1_regression": True,
        },
        "invariants": {
            "no_a48_a49_reuse": True, "no_a50_viewer_window_reuse": True,
            "source_reference_must_remain_immutable": True,
            "reader_ids_must_be_opaque": True,
        },
    }
    (EXP / "split.json").write_text(json.dumps(split, indent=2) + "\n")
    print(json.dumps(split, indent=2))


if __name__ == "__main__":
    main()
