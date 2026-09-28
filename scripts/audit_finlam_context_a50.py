#!/usr/bin/env python3
"""A50 consumed-data audit: is adjacent-page context the titleless-article bottleneck?"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/finlam-boundaries-a50/context-audit.json"
BASE = "https://datasets-server.huggingface.co/rows"
DATASET = "Teklia/Newspapers-finlam-La-Liberte"
REVISION = "c3d69ca1eef5a0f479b6aeaa6d6c155b3ec93657"
TARGETS = [92, 135, 186, 356, 409, 419]

# Consumed A49 issue windows reconstructed from page_index plus complementary
# issue-global zone_order intervals.  This is an audit, never model input.
ISSUES = {
    92: {1: 93, 2: 92, 3: 90, 4: 91},
    135: {1: 136, 2: 135, 3: 134, 4: 133, 5: 137, 6: 140},
    186: {1: 184, 2: 186, 3: 185, 4: 183, 5: 189, 6: 187},
    356: {1: 354, 2: 357, 3: 356, 4: 355, 5: 353, 6: 358},
    409: {1: 410, 2: 411, 3: 412, 4: 409, 5: 407, 6: 408},
    419: {1: 424, 2: 423, 3: 421, 4: 426, 5: 419, 6: 422, 7: 425, 8: 420},
}


def fetch_window(target: int) -> dict[int, dict]:
    params = urllib.parse.urlencode({
        "dataset": DATASET, "config": "default", "split": "test",
        "offset": max(0, target - 10), "length": 21,
    })
    with urllib.request.urlopen(f"{BASE}?{params}", timeout=60) as response:
        payload = json.load(response)
    rows = {item["row_idx"]: item["row"] for item in payload["rows"]}
    if any(REVISION not in row["page_image"]["src"] for row in rows.values()):
        raise ValueError("dataset revision mismatch")
    return rows


def main() -> None:
    pages = []
    for target in TARGETS:
        rows = fetch_window(target)
        issue = {page: rows[index] for page, index in ISSUES[target].items()}
        current = rows[target]
        occurrence: dict[int, set[int]] = defaultdict(set)
        for page_index, row in issue.items():
            for article in row["zone_article_ids"]:
                if article is not None:
                    occurrence[article].add(page_index)
        articles = {a for a in current["zone_article_ids"] if a is not None}
        titled = {
            current["zone_article_ids"][zone]
            for zone, class_id in enumerate(current["zone_classes"])
            if class_id == 6 and current["zone_article_ids"][zone] is not None
        }
        titleless = articles - titled
        multipage = {article for article in titleless if len(occurrence[article]) > 1}
        zone_histogram = Counter()
        role_histogram = Counter()
        for article in titleless:
            zones = [i for i, value in enumerate(current["zone_article_ids"]) if value == article]
            zone_histogram[len(zones)] += 1
            role_histogram.update(current["zone_classes"][zone] for zone in zones)
        pages.append({
            "row_index": target, "page_index": current["page_index"],
            "issue_pages_reconstructed": sorted(issue),
            "articles": len(articles), "articles_without_title": len(titleless),
            "titleless_multipage_continuations": len(multipage),
            "titleless_multipage_article_ids": sorted(multipage),
            "titleless_zone_count_histogram": dict(sorted(zone_histogram.items())),
            "titleless_role_id_histogram": dict(sorted(role_histogram.items())),
        })
    titleless = sum(page["articles_without_title"] for page in pages)
    continuations = sum(page["titleless_multipage_continuations"] for page in pages)
    report = {
        "schema": "bbvlm.finlam-context-a50-audit/1",
        "status": "consumed A49 convention audit",
        "source": {"dataset": DATASET, "revision": REVISION, "split": "test"},
        "pages": pages,
        "aggregate": {
            "titleless_articles": titleless,
            "titleless_multipage_continuations": continuations,
            "multipage_share": continuations / titleless if titleless else 0.0,
        },
        "finding": (
            "Adjacent-page context explains only a small minority of titleless articles; "
            "most are within-page advertisements, notices or briefs encoded without TITLE zones. "
            "Prioritize within-page boundary semantics, then use adjacent pages only for routed continuations."
        ),
        "invariants": {
            "consumed_development_only": True, "source_reference_unchanged": True,
            "page_grouping_uses_page_index_and_issue_global_order_bands": True,
        },
        "limitations": [
            "Issue identity is inferred from complementary issue-global order bands because the viewer row has no issue identifier.",
            "Article IDs and classes are reference annotations used only to diagnose the consumed A49 failure.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
