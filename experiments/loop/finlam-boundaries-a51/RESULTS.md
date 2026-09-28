# A51 — frozen semantic-boundary pilot

## Protocol status

Eight Finlam rows were frozen before their content was opened:
`216, 164, 201, 287, 48, 367, 306, 50`. All A48–A50 pages were excluded.
Only rows 216 and 164 were opened for this pilot; the other six remain reserved.
The CPU router reads only region roles and geometry. It never reads provider
article identifiers. One blind Luna pass classified 149 opaque boundary crops
on 26 sheets.

A mechanical amendment made after image opening but before model output or
reference scoring preserves floating-point polygon extents. Integer rounding
had collapsed one very thin region to zero width. The pilot is therefore
independent of provider article labels at routing time, but not a pristine
implementation freeze.

## Results

| row | boundary F1 | global pair order | within-article order | title baseline article F1 | title + Luna article F1 |
|---:|---:|---:|---:|---:|---:|
| 216 | 0.6667 | 0.8677 | 0.9878 | 0.7148 | **0.8397** |
| 164 | 0.3025 | 0.7656 | 0.9646 | **0.2604** | 0.1249 |
| macro | 0.4846 | 0.8167 | 0.9762 | **0.4876** | 0.4823 |

Frozen gates were macro article F1 ≥0.80, global pair order ≥0.90,
within-article order ≥0.98, improvement over the title baseline, and no
per-page article-F1 regression. Every gate fails.

Row 164 is the decisive counterexample: Luna creates 83 false-positive cuts
and no false negatives. Its visual/semantic partition is locally plausible,
but the provider reference groups 173 zones into article 123 and 67 zones into
article 124. The task therefore mixes at least two notions: independently
retrievable semantic items and large provider containers/sections.

## Decision

Reject the A50 boundary policy as a general article splitter. Preserve its
positive row-216 result, but do not retune on either opened pilot page and do
not consume the six reserved rows until the target ontology is fixed.

The next OLR representation must model two levels explicitly:

1. provider-compatible containers/sections, scored against the immutable
   Finlam article IDs;
2. independently retrievable semantic items, evaluated under a separately
   adjudicated relevance task.

ALTO keeps physical `TextBlock`/`TextLine`/`String` geometry. The two logical
levels belong in METS `structMap` (or an external graph referenced from METS),
with provenance and confidence rather than destructive relabelling.

Cost: one Luna pass, two pages, 26 images, 149 queried transitions. No Sol
escalation, OCR pass, or coordinate-generation request was used.
