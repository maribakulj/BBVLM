# A65 — geometry-only crop ablation on Chronicling validation

Frozen before geometry scoring on 28 September 2026. Use all 50 official
Validation pages at the A58 immutable XML snapshot. Never open the 100 Test
pages, images or transcription values. This is an oracle-annotation structural
experiment, not detector inference, independent OCR validation, or OLR truth.

Hypothesis: class-specific crop masks can omit parts of line annotations;
replacing polygons by enclosing rectangles can admit neighbouring regions.
Compare each valid TextLine polygon with (1) its parent TextRegion polygon,
(2) the parent's axis-aligned bounding rectangle, and (3) the union of all valid
TextRegion polygons on the page. Report missing area fractions at >1% and >5%,
all invalid geometries separately, by page and in aggregate. The union is an
oracle diagnostic, not a proposed whole-page OCR mask or a safe reading order.
No threshold is tuned, no invalid polygon repaired, no source XML overwritten.

For each valid TextRegion, measure polygon area / bounding rectangle area,
and added rectangle area intersecting other TextRegion polygons but outside
its own polygon. Report overlap pairs and regions at >1% foreign area. This
measures annotation-area interference, not actual ink loss or transcription.

Code must verify A58 per-file hashes, split disjointness and 50-page inventory;
synthetic tests cover a contained line, a boundary-crossing line and a concave
region whose rectangle captures an unrelated region. Use Shapely 2.1.2 CPU.
All original metric profiles and all seven scientific gates remain unchanged.

Primary reading: Schultze et al., arXiv:2401.16845v4 (13 June 2025), sections
3, 4 pipeline, A.4.2, A.5 and A.7.2, reread 28 September 2026. These distinguish
expert cross-checked region polygons from selectively corrected line polygons,
automatic reading order and future article truth. Current code tree
8a4b7c5613a888cde7d092e38b1841f3bff3f617: slicing_export.py and
yolo/preprocess.py read fully. The latter replaces polygons with their bounds;
the former's optional export masks to label 3 (paragraph). This does not imply
every upstream execution uses that optional export.

Claude head rechecked before hypothesis: 76056c5c1957e0de4232f0aef1f6cbc7f2893402,
unchanged. Codex remains on codex/autonomous-research-a34, parent A64 20c5086;
master remains 60b8ed3. Never merge or update master/main.
