# A32: component refinement, development only

Frozen before executing the new variants, 2026-09-27. A28's eight pages
(two works, 261 lines, 1753 words) are consumed development material.
The defect is neighboring-line ink and bleed-through included by raw Otsu.

Compare existing native PERO, forced CTC and raw Otsu with three fixed CPU
ablations: area filter; body-band components; body-band plus satellites.
Parameters live in `bbvlm.component_boxes.PARAMETERS`. No sweep or revision
after scores in this experiment. Infer a dense band from line image pixels,
retain whole components (not vertically clipped stems), optionally attach
nearby detached marks. CTC midpoint cells unchanged. An empty filtered cell
falls back to its raw ink, then original forced geometry.

Constructor sees only line image, line rectangle, existing forced boxes and
mode. Evaluator uses reference word boxes. Existing forced boxes depend on
oracle text/token order, and line rectangles are oracle. Their baseline is
synthetic at 0.8 of line height: this is NOT an end-to-end PERO comparison.
No fresh OCR/VLM inference, no training, no reference replacement.

Report mean IoU, IoU50/80 recall, boundary error, per-page and per-work values,
paired improvements/regressions, fallback counts and incremental CPU time.
Inspect best improvements and worst regressions visually. A mean gain alone
cannot demonstrate preserved ascenders or perfect boxes. No completion gate
can pass from this development experiment. Next candidate needs an unopened
independent sample and predicted line/text evaluation.

Implementation amendment before reading corpus scores: the synthetic test
found that bounding-box proximity to a wide joined component can accept
distant noise. Replace it with rectangular dilation of the actual core pixels,
using the same fixed gap fractions. The first evaluator had already run while
the failing test was reported; preserve that uninspected output as `initial/`.
This is a documented development amendment, not a claim of pristine holdout
preregistration. No corpus-driven parameter change.
