"""Deterministic semantic-unit proposals for simple columnar pages."""
from __future__ import annotations

from .order import infer_column_major_order


def refine_stream_roles_by_height(regions, page_bbox, coarse_roles, *,
                                  max_header_height_page_ratio):
    """Refine STREAM into HEADER/TEXT with one frozen normalized threshold."""
    ids = [r["id"] for r in regions]
    if len(ids) != len(set(ids)):
        raise ValueError("region IDs must be unique")
    if set(coarse_roles) != set(ids):
        raise ValueError("coarse_roles must cover every region")
    if max_header_height_page_ratio <= 0:
        raise ValueError("max_header_height_page_ratio must be positive")
    page_height = float(page_bbox[3]) - float(page_bbox[1])
    if page_height <= 0:
        raise ValueError("page height must be positive")
    roles = {}
    for region in regions:
        rid = region["id"]
        role = coarse_roles[rid]
        if role == "STREAM":
            height = float(region["bbox"][3]) - float(region["bbox"][1])
            if height < 0:
                raise ValueError("region height must be non-negative")
            role = "HEADER" if height / page_height <= max_header_height_page_ratio else "TEXT"
        roles[rid] = role
    return roles


def refine_stream_roles_by_typography(regions, coarse_roles, typography_by_region, *,
                                      max_header_line_count,
                                      min_median_line_height_page_ratio,
                                      min_uppercase_ratio):
    """Refine STREAM into HEADER/TEXT from internal line typography."""
    ids = [r["id"] for r in regions]
    if len(ids) != len(set(ids)):
        raise ValueError("region IDs must be unique")
    expected = set(ids)
    if set(coarse_roles) != expected:
        raise ValueError("coarse_roles must cover every region")
    if set(typography_by_region) != expected:
        raise ValueError("typography_by_region must cover every region")
    if max_header_line_count < 1:
        raise ValueError("max_header_line_count must be positive")
    if min_median_line_height_page_ratio < 0:
        raise ValueError("min_median_line_height_page_ratio must be non-negative")
    if not 0 <= min_uppercase_ratio <= 1.01:
        raise ValueError("min_uppercase_ratio must be between 0 and 1.01")
    roles = {}
    for rid in ids:
        role = coarse_roles[rid]
        features = typography_by_region[rid]
        line_count = int(features["line_count"])
        line_height = float(features["median_line_height_page_ratio"])
        uppercase_ratio = float(features["uppercase_ratio"])
        if line_count < 0 or line_height < 0 or not 0 <= uppercase_ratio <= 1:
            raise ValueError("invalid typography features")
        if role == "STREAM":
            is_short = 0 < line_count <= max_header_line_count
            is_emphasized = (
                line_height >= min_median_line_height_page_ratio
                or uppercase_ratio >= min_uppercase_ratio
            )
            role = "HEADER" if is_short and is_emphasized else "TEXT"
        roles[rid] = role
    return roles


def group_header_units(regions, page_bbox, roles, eligible_region_ids, *,
                       gap_ratio=0.14, top_exclusion_ratio=0.055,
                       max_anchor_width_ratio=0.55,
                       min_anchor_width_ratio=0.0,
                       assign_by_overlap=False,
                       merge_overlapping_headers=True):
    """Partition supplied regions using roles and a frozen column order.

    Within each inferred column, a header opens a unit. Consecutive header
    regions stay together only when their vertical boxes overlap; this covers
    multi-block titles without merging the next item. Text before the first
    header is retained as a continuation unit. Masthead fragments share one
    unit; excluded/OTHER/UNKNOWN/ADVERT regions are conservative singletons.
    """
    ids = [r["id"] for r in regions]
    expected = set(ids)
    if len(ids) != len(expected):
        raise ValueError("region IDs must be unique")
    if set(roles) != expected:
        raise ValueError("roles must cover every region")
    eligible = list(eligible_region_ids)
    if len(eligible) != len(set(eligible)) or not set(eligible) <= expected:
        raise ValueError("eligible_region_ids must be a unique subset")
    by_id = {r["id"]: r for r in regions}
    order = infer_column_major_order(
        regions, page_bbox, gap_ratio=gap_ratio,
        top_exclusion_ratio=top_exclusion_ratio,
        max_anchor_width_ratio=max_anchor_width_ratio,
        min_anchor_width_ratio=min_anchor_width_ratio,
        assign_by_overlap=assign_by_overlap)
    eligible_set = set(eligible)
    groups = []
    masthead = [rid for rid in order["ordered_region_ids"] if roles[rid] == "MASTHEAD"]
    if masthead:
        groups.append({"kind": "MASTHEAD", "region_ids": masthead})
    # Regions not routed into the reading stream are never silently attached to
    # content, except that masthead fragments form their explicit physical unit.
    for rid in order["ordered_region_ids"]:
        if rid not in eligible_set and roles[rid] != "MASTHEAD":
            groups.append({"kind": roles[rid] if roles[rid] in {"ADVERT", "OTHER"} else "UNKNOWN",
                           "region_ids": [rid]})
    for column in sorted(set(order["column_by_region"].values())):
        current = []
        sequence = [rid for rid in order["ordered_region_ids"]
                    if rid in eligible_set
                    and roles[rid] != "MASTHEAD"
                    and order["column_by_region"][rid] == column]
        for rid in sequence:
            role = roles[rid]
            if role in {"ADVERT", "OTHER", "UNKNOWN", "MASTHEAD"}:
                if current:
                    groups.append({"kind": "ARTICLE", "region_ids": current}); current = []
                groups.append({"kind": role if role in {"ADVERT", "OTHER", "MASTHEAD"} else "UNKNOWN",
                               "region_ids": [rid]})
                continue
            start_new = False
            if role == "HEADER" and current:
                header_ids = [x for x in current if roles[x] == "HEADER"]
                has_body = any(roles[x] == "TEXT" for x in current)
                overlaps_header = any(
                    min(by_id[rid]["bbox"][3], by_id[x]["bbox"][3])
                    > max(by_id[rid]["bbox"][1], by_id[x]["bbox"][1])
                    for x in header_ids)
                start_new = has_body or not (merge_overlapping_headers and overlaps_header)
            if start_new:
                groups.append({"kind": "ARTICLE", "region_ids": current}); current = []
            current.append(rid)
        if current:
            groups.append({"kind": "ARTICLE", "region_ids": current})
    flat = [rid for group in groups for rid in group["region_ids"]]
    if len(flat) != len(set(flat)) or set(flat) != expected:
        raise AssertionError("semantic grouping must partition every region")
    return {"groups": groups, "order": order}
