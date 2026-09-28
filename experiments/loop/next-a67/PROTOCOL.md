# A67 — visual audit of A66 fragmentation, frozen 2026-09-28

After A66 commit53aea20 and checkpoint51, Claude rechecked unchanged76056c5.
No new detector hypothesis: follow-up diagnostic to distinguish polygon-area
fragmentation from visible crop clipping. A65/A66 source limitations apply.
One authorized Luna visual reader, no simultaneous model ensemble. Not human
adjudication, independent validation, OCR CER or newly established ground truth.

Selection fixed before viewing: for each page in A66 with a fragmented line
at1024 under text_like policy, sort line IDs lexically and take the first.
Four pages qualify. For that line choose the predicted text-like box with
greatest polygon intersection. These are oracle-selected consumed diagnostics.
Opaque random-looking IDs and shuffled case order in reader inputs; no source
file names, reference text, XML, detector names, scores or expected conclusions.

Three native-resolution views per case: exact enclosing integer crop of the
chosen predicted box; local unmarked source context around selected line bounds;
same context with red crop-boundary segments (where they fall in context).
Context is line bounds plus100 pixels each side, clipped to source image.
No image resampling or normalization. Red overlays are separate files and never
modify the unmarked images. No source XML/image writes.

Reader must inspect all12 images, report each view path and return four IDs:
visible_clipping yes/no/uncertain, evidence, affected_edge, whether additional
text in context is separate content, confidence, and uncertainties. No requirement
to agree with a metric. Parent checks schema/IDs/hashes and records limitations.
Evidence snippets are observations, never substitute GT. Escalate only if a
specific unresolved observation materially affects the next crop policy.

Sources: Chronicling2401.16845v4 section A.7.2 (selective line correction and
layout-class cuts), DocLayout-YOLO current predictor32a8ec2 (native box rescaling).
These were actually read in A65/A66; A67 introduces no new paper claim. Summaries
remain separately accessible in PAPER_SUMMARIES.md. No gate or normalization changes.
