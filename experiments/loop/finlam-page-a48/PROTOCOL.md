# A48 — frozen page-level French newspaper structure evaluation

Three rows from the official Finlam–La Liberté test split are selected solely
by hashing their integer indices before any row content, image, annotation or
ordered ID is opened.  The dataset revision and split size are pinned.

The first inspection must determine the exact schema and whether reference
order/article membership are genuinely present.  Predictions shown to a VLM
must use opaque, shuffled IDs; a request must never leak reference order through
ID numbering, array position, filename, prompt, or crop sequence.  One Luna
reader is primary.  Sol is permitted only after a documented ambiguity or
structural failure and receives no prior answer.

Reference annotations remain immutable.  Geometry, reading order, article
grouping, OCR, metadata and retrieval are scored separately.  Three pages are
an engineering transfer experiment, not sufficient to open a global gate.
