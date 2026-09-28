"""Deterministic reading-order baselines for already detected regions."""
from __future__ import annotations
from statistics import median


def infer_column_major_order(regions, page_bbox, *, gap_ratio=0.14,
                             top_exclusion_ratio=0.055,
                             max_anchor_width_ratio=0.55,
                             min_anchor_width_ratio=0.0,
                             assign_by_overlap=False):
    """Infer a left-to-right, top-to-bottom column order from region boxes.

    This deliberately uses geometry only.  It is suitable as a cheap baseline
    or proposal, not as a universal reading-order solution for interleaved
    narratives. Callers must exclude mastheads/metadata that are not part of
    the reading stream before promoting the returned edges. ``regions`` must
    contain unique ``id`` and xyxy ``bbox``.
    """
    ids = [r["id"] for r in regions]
    if len(ids) != len(set(ids)):
        raise ValueError("region IDs must be unique")
    x0, y0, x1, y1 = page_bbox
    width, height = x1 - x0, y1 - y0
    if width <= 0 or height <= 0:
        raise ValueError("page bbox must be non-empty")
    for region in regions:
        box = region.get("bbox")
        if not isinstance(box, (list, tuple)) or len(box) != 4 or box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError(f"invalid region bbox: {region.get('id')}")
    anchor_regions = sorted((
        r
        for r in regions
        if r["bbox"][1] >= y0 + top_exclusion_ratio * height
        and r["bbox"][2] - r["bbox"][0] <= max_anchor_width_ratio * width
        and r["bbox"][2] - r["bbox"][0] >= min_anchor_width_ratio * width
    ), key=lambda r:r["bbox"][0])
    if not anchor_regions:
        anchor_regions = sorted(regions,key=lambda r:r["bbox"][0])
    clusters = []
    for region in anchor_regions:
        x=region["bbox"][0]
        if not clusters or x - clusters[-1][-1]["bbox"][0] > gap_ratio * width:
            clusters.append([region])
        else:
            clusters[-1].append(region)
    anchors = [median(r["bbox"][0] for r in cluster) for cluster in clusters]
    spans = [[min(r["bbox"][0] for r in cluster),max(r["bbox"][2] for r in cluster)] for cluster in clusters]
    def column(region):
        x = region["bbox"][0]
        if assign_by_overlap:
            overlaps=[max(0,min(region["bbox"][2],span[1])-max(region["bbox"][0],span[0])) for span in spans]
            if max(overlaps)>0:
                return max(range(len(spans)),key=lambda i:(overlaps[i],-abs(x-anchors[i]),-i))
        return min(range(len(anchors)), key=lambda i: (abs(x - anchors[i]), i))
    ordered = sorted(regions, key=lambda r: (column(r), r["bbox"][1], r["bbox"][0], r["id"]))
    ordered_ids = [r["id"] for r in ordered]
    return {
        "ordered_region_ids": ordered_ids,
        "reading_order": [
            {"before": before, "after": after}
            for before, after in zip(ordered_ids, ordered_ids[1:])
        ],
        "column_by_region": {r["id"]: column(r) for r in regions},
        "column_anchors_x": anchors,
        "column_spans_x": spans,
        "parameters": {
            "gap_ratio": gap_ratio,
            "top_exclusion_ratio": top_exclusion_ratio,
            "max_anchor_width_ratio": max_anchor_width_ratio,
            "min_anchor_width_ratio": min_anchor_width_ratio,
            "assign_by_overlap": assign_by_overlap,
        },
    }


def infer_recurrent_column_order(
    regions,
    page_bbox,
    *,
    body_roles=("TEXT", "ILLUSTRATEDTEXT"),
    narrow_width_ratio=0.22,
    fine_cluster_width_fraction=0.25,
    merge_anchor_width_fraction=0.50,
    min_support=3,
):
    """Infer newspaper columns from recurrent body-region left edges.

    The modal body width sets both clustering scales. Parameters were developed
    on consumed Finlam A48 and require unopened-page validation before use as a
    promoted default.
    """
    ids = [r["id"] for r in regions]
    if len(ids) != len(set(ids)):
        raise ValueError("region IDs must be unique")
    x0, y0, x1, y1 = page_bbox
    width, height = x1 - x0, y1 - y0
    if width <= 0 or height <= 0:
        raise ValueError("page bbox must be non-empty")
    if min_support < 1:
        raise ValueError("min_support must be positive")
    eligible = []
    for region in regions:
        box = region.get("bbox")
        if not isinstance(box, (list, tuple)) or len(box) != 4 or box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError(f"invalid region bbox: {region.get('id')}")
        if (region.get("role") in body_roles
                and (box[2] - box[0]) / width < narrow_width_ratio):
            eligible.append(region)
    if not eligible:
        raise ValueError("no narrow body regions for recurrent-column inference")
    modal_width = median((r["bbox"][2] - r["bbox"][0]) / width for r in eligible)
    fine_gap = fine_cluster_width_fraction * modal_width * width
    raw_clusters = []
    for region in sorted(eligible, key=lambda r: r["bbox"][0]):
        if not raw_clusters or region["bbox"][0] - raw_clusters[-1][-1]["bbox"][0] > fine_gap:
            raw_clusters.append([region])
        else:
            raw_clusters[-1].append(region)
    supported = [cluster for cluster in raw_clusters if len(cluster) >= min_support]
    if not supported:
        raise ValueError("no recurrent column start has minimum support")
    merged = []
    merge_gap = merge_anchor_width_fraction * modal_width * width
    for cluster in supported:
        anchor = median(r["bbox"][0] for r in cluster)
        if merged and anchor - median(r["bbox"][0] for r in merged[-1]) < merge_gap:
            merged[-1].extend(cluster)
        else:
            merged.append(list(cluster))
    anchors = [median(r["bbox"][0] for r in cluster) for cluster in merged]

    def column(region):
        return min(range(len(anchors)), key=lambda i: (abs(region["bbox"][0] - anchors[i]), i))

    ordered = sorted(regions, key=lambda r: (column(r), r["bbox"][1], r["bbox"][0], r["id"]))
    ordered_ids = [r["id"] for r in ordered]
    return {
        "ordered_region_ids": ordered_ids,
        "reading_order": [
            {"before": before, "after": after}
            for before, after in zip(ordered_ids, ordered_ids[1:])
        ],
        "column_by_region": {r["id"]: column(r) for r in regions},
        "column_anchors_x": anchors,
        "modal_body_width_ratio": modal_width,
        "parameters": {
            "body_roles": list(body_roles),
            "narrow_width_ratio": narrow_width_ratio,
            "fine_cluster_width_fraction": fine_cluster_width_fraction,
            "merge_anchor_width_fraction": merge_anchor_width_fraction,
            "min_support": min_support,
        },
    }
