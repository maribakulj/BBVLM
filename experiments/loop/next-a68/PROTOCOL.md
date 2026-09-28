# A68 — bounded ink-edge repair (consumed development)

## Status and branch barrier

- Claude branch checked before the hypothesis: `76056c5c1957e0de4232f0aef1f6cbc7f2893402`, unchanged.
- Codex parent: `b2d7d65a6914597a9d27d84e5c0d5b69d3a2eb4b`.
- `master`: `60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`, untouched.
- The five A66 Validation pages and four A67 oracle-selected cases are consumed development data. The 100 Chronicling Test pages remain unopened.

## Frozen hypothesis

DocLayout-YOLO's native 1024-pixel text-like boxes sometimes cut ink at an edge. Compare three immutable crop policies on all five consumed pages:

1. `native`: rasterized detector rectangle (`floor` minima, `ceil` maxima);
2. `fixed`: add the same page-scaled padding on every side;
3. `ink_crossing`: add space on a side only when an 8-connected Otsu foreground component has at least two pixels in the two-pixel inner border strip and at least two pixels outside that exact border.

The maximum extension for both non-native policies is `max(4, round(0.003 * min(page_height, page_width)))` pixels. Components smaller than three pixels are ignored. No morphology, OCR, XML geometry, text, confidence tuning, or VLM judgment enters candidate construction. Parameters are frozen before scoring.

## Measurements

After `candidates.json` is durably written, open Validation XML only for scoring:

- line-polygon area covered by the best single crop (mean and counts below 0.50/0.95);
- added crop area;
- overlap with non-dominant annotated regions, with dominant region fixed from the native crop;
- number and side of image-driven changes;
- a visual overlay of the two A67 Sol-positive clipping cases plus the largest image-driven expansion.

These are annotation-area diagnostics. Foreground connectivity does not prove semantic ownership, and region/line polygons do not certify perfect ALTO boxes. No OCR CER, OLR, metadata or retrieval gate can be promoted in A68.

## Promotion rule

Do not promote either repair from A68. Use the result only to select at most one frozen candidate for a separate diverse, unopened validation. Reject a method that gains line coverage by materially increasing foreign-region intrusion.
