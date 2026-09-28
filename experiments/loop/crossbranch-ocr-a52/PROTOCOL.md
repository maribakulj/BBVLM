# A52 — exact-input cross-branch OCR replication

Frozen before the Luna read. This is a **development replication**, not an
independent validation: both pages were already consumed by Claude O02. The
purpose is to isolate why Opus reached 0% adjudicated CER on a clean page while
earlier BBVLM Luna/Sol readers did not reliably do so.

## Pages and conditions

- `A52-P01`: clean French Roman print (`borrdisc` page 19), reported by Claude
  as 0% adjudicated CER in both Opus readings.
- `A52-P02`: hard German Fraktur (`drabnota` page 389), reported by Claude as
  non-zero even after adjudication.
- Identical view policy for both: whole page capped at 1350 px, source-resolution
  horizontal bands of 600 px with 120 px overlap, plus overlapping half-band
  crops enlarged 1.6×.

One Luna reader sees only opaque IDs and images. It does not see references,
Claude outputs, corpus names, scores or expected differences. Sol is reserved
for localized residual adjudication only; it is not run in parallel.

## Scoring

Report strict, diplomatic and search-normalized CER separately. Line matching
is order-independent so CER does not absorb OLR. Compare against both the
immutable distributed PAGE reference and Claude's adjudicated derivative.
Neither derivative nor model agreement is called ground truth. Report exact
edits, page-level non-regression, images/passes, and whether each residual is a
glyph error, convention difference, layout omission, or reference dispute.

The hypothesis succeeds only if the same Luna protocol reaches 0 adjudicated
normalized edits on P01 without increasing unsupported content, and if P02
improves over the reported Opus O02 best while preserving diplomatic signs.
