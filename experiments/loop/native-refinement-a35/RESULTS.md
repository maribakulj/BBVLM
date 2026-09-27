# A35 — Refinement with recognized words, not reference transcription

2026-09-27. Completed diagnostic on already consumed A28/A34 pages. No new VLM or recognizer inference. This removes the oracle-transcription dependency from the refiner, but keeps reference line rectangles and synthetic baselines. It is not an independent end-to-end validation.

## Measurement

All candidates use the same geometry-only Hungarian matching, with unmatched reference words retained in recall denominators. A32 parameters are unchanged; no tuning against these results. Native word text, order and cardinality are preserved, including one empty OCR line.

| Dataset | GT / recognized words | Native mean IoU | Refined mean IoU | Native recall IoU≥0.8 | Refined recall IoU≥0.8 | Oracle-text A32 recall IoU≥0.8 |
|---|---:|---:|---:|---:|---:|---:|
| french-word-gt-a28 | 1753 / 1761 | 0.582591 | 0.892025 | 11.07% | 80.66% | 81.75% |
| word-transfer-a34 | 4759 / 4768 | 0.654863 | 0.803298 | 19.04% | 55.96% | 58.94% |

No page loses aggregate IoU≥0.8 recall across these 20 pages, but individual regressions remain. The fixed native assignment separates actual box changes from assignment changes: French 1,679 improve, 55 regress, including 3 losses greater than 0.1 IoU; German/Latin 4,109 improve, 567 regress, including 17 losses greater than 0.1. This is not perfect geometry.

Requiring BOTH exact token text and IoU≥0.8 gives French 166/1,753 → 1,284/1,753 (9.47% → 73.25%) and German/Latin 540/4,759 → 2,003/4,759 (11.35% → 42.09%). Text uses the existing `glyph_decomposition_v1` diagnostic convention, not a claimed Gallica/Exalead normalization. No OCR text was changed and no CER improvement is claimed. Slight differences in matched exact-text counts arise from geometry assignment, not recognition.

The oracle-text A34 comparator is rescored with the same matching here; its mean IoU is .812306, versus the previous index-based .812303. Do not compare mismatched scoring protocols.

## Visual failure audit

`regressions-clean.png` was actually inspected after scoring, using eight worst fixed-assignment losses; `visual-audit-cases.json` retains IDs, rectangles and scores. This is a post-score diagnostic, not independent adjudication.

- `P00000027_l744` (Ist) and `P00000027_l3183` (Hr.): extension into neighboring lower-line ink.
- `P00000024_l868` (predicted I., reference 1.) and `P00000024_l1523` (O.): adjacent left ink enters the refined crop. The I./1. disagreement is lexical and remains unchanged.
- `P00000035_l11` (ij): extra left mark, with ambiguous detached small marks; no reference correction inferred.
- `P00000024_l2860` (dieſe): neighboring upper/lower ink enlarges the box.
- `P00000026_l599`: a visible trailing comma in the native crop is lost by refinement.
- French `P00000273_l392` (4): refinement recovers the numeral's clipped right edge but expands excessively leftward. Lower IoU here must not be equated with uniformly worse legibility.

Original annotations and native predictions are unchanged. Boxes can improve on average while removing meaningful punctuation; this prevents promotion to a perfect-box claim.

## Cost and decision

Incremental CPU refinement: 0.691 s for 261 French lines, 3.593 s for 515 German/Latin lines; total evaluation 7.477 s. Historical recognizer prerequisites remain 36.336 s/261 forwards and 10.874 s/515 forwards, respectively. Native ALTO export was not separately metered. Cached recognition is not free. No new VLM pass or model installation.

All five recorded invariants pass: protected input hashes unchanged; native text/order/cardinality preserved; no reference word text/boxes in refiner; no new inference; no reference replacement. Two new metric tests ensure wrong text cannot receive joint success and missing/empty predictions remain penalized.

Retain A32 as an experimental cheap geometry stage. Its benefit largely survives recognized text, so a VLM is not needed to obtain this particular box gain. Its value must instead be measured through recognition/OLR/evidence-rich semantic output. Next priority is predicted line geometry and an unopened diverse reference set, then independent lexical adjudication and joint OCR/OLR evaluation. Do not retune consumed A28/A34 or promote their references to perfect truth. All seven project completion gates remain false.
