# A69 — frozen transfer of A68 ink-edge repair

Claude was rechecked at `76056c5c1957e0de4232f0aef1f6cbc7f2893402`;
Codex parent is `42e8c5ef6d3447d14522fd94d57179253e122dca` and master remains
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. No merge or competing code is used.

All 50 official Validation XML geometries were already consumed by A65. Calling
another subset of them unopened would be false. A69 therefore freezes ten
official **Training** pages as a BBVLM transfer holdout: ten titles/styles from
1617–1933, no A66 image, no Test page, and no prior detector/crop score. A58 did
perform a corpus-wide structural XML audit; this prevents a pristine-corpus
claim but did not tune A68. The 100 official Test pages remain unopened.

The A68 rule and parameters are unchanged: 1024-pixel DocLayout-YOLO, text-like
classes, rasterized native boxes, fixed padding and `ink_crossing` with
`max(4, round(.003*min(H,W)))`, 8-connectivity, area >=3, two-pixel inner strip,
and >=2 pixels on both sides. Images and predictions are saved first;
`candidates.json` is written and hashed before any transfer XML is opened.

Frozen local promotion gate for `ink_crossing` only (not a global completion
gate): no increase in lines below 50 %, at least 20 % relative reduction in
lines below 95 %, added area <=60 % of fixed padding, boxes with >1 % foreign
addition <= fixed, foreign fraction of added area <= fixed +2 percentage points,
and no per-page mean-coverage regression. Passing permits use as a bounded crop
proposal; it does not certify perfect boxes, semantic ownership, OCR or OLR.

No new scientific paper is required: this is a direct transfer of the A68
hypothesis and its already recorded readings. No heavy dependency is added.
