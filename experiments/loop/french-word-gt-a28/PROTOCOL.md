# A28 — French SBB word-box and OCR reference

## Purpose

Evaluate the frozen A25 CTC-separator plus raw-line-Otsu word-box candidate on
all eight pages of the only two works catalogued `fre` in the pinned
OCR-D/SBB tree: `borrdisc_689809840` and `catapabin_657601357`. These works and
pages have not appeared in A18, A22, or A25.

## Freeze and reference

Selection uses only the pinned Git tree and catalogue language audit. Before
any of the eight PAGE XML or TIFF members is downloaded, freeze this protocol,
the split, opener, wrapper evaluator, unchanged A25 candidate core, and tree
hash. On opening, verify every Git blob before parsing. Fail closed if any page
has no TextLine, Word, word polygon, or line transcription, or if line text is
not the whitespace join of its Word texts.

The source is provider ground truth followed by SBB post-correction/manual page
inspection. The stated 99.95% capture target is not a perfection certificate.
Original files remain immutable; predictions never replace reference text or
polygons.

## Candidate and metrics

The candidate is exactly A25: oracle line polygon and reference text are aligned
to the frozen PERO recognizer CTC; adjacent forced word intervals meet at their
midpoint; one Otsu threshold over the source line rectangle tightens each cell
to observed ink extents. Native PERO boxes and forced CTC boxes are baselines.

Report strict/decomposed native PERO CER, reference/predicted word counts, mean
matched IoU, IoU>=0.5 and IoU>=0.8 precision/recall, boundary errors, all-word
line success, per-page results, runtime, and private-use inventory.

The conditional box gate requires, on every page: no omission, recall@0.5 = 1,
recall@0.8 >= 0.90, mean IoU >= 0.90, and strict improvement over both baselines
at IoU@0.8 with non-inferiority at IoU@0.5 and mean IoU. Passing remains
conditional on oracle lines/text/token order and does not establish end-to-end
layout, OCR CER=0, or perfect ground truth.

