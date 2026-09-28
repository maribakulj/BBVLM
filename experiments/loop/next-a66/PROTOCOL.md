# A66 — image-only DocLayout-YOLO transfer, frozen 2026-09-28

After A65 commit 4706e6d and checkpoint version 50. Claude rechecked at
76056c5c1957e0de4232f0aef1f6cbc7f2893402, unchanged. No main/master writes.

Measured motivation: A65 shows parent polygons/rectangles trade line-annotation
coverage for neighbouring-region intrusion. Now test real predicted rectangles
without any reference supplied to the detector. This is a development transfer
pilot, not an independent final validation or an OCR experiment.

Five official Validation pages, selected by named publication/date to include
different years and an illustrated title before downloading images:
Berliner_Boersen_Zeitung_1857-04-06_0001,
Bonner_Zeitung_1891-09-16_0001, Der_Bazar_1856-01-15_0004,
Dresdner_Journal_1898-05-27_0001,
Hildener_Rundschau_Illustrierte_1930-10-26_0006.
The 100 Test pages remain unopened. All five pages become consumed development
examples after this pilot. This sample is small and purposive, not representative.

Pinned existing DocStructBench weights: revision
8c3299a30b8ff29a1503c4431b035b93220f7b11, SHA256
9a2ee0220fe3d9ad31b47e1d9f1282f46959a54e4618fce9cffcc9715b8286e2.
Two preset whole-page resolutions: 1024 and 1600; confidence .2, max_det=300,
CPU, four threads, one image at a time, no padding or posthoc box correction.
No OCR, VLM or language-model call. Reference XML geometry is loaded only after
all predictions are written. Never read TextEquiv values or alter source XML.

Report separately for all boxes and text-like boxes (all except figure/table):
single-box coverage and union coverage of each valid TextLine polygon;
missed (union <.5), incomplete (single <.95), fragmented (union >=.95 but
single <.95). Counts are annotation-area proxies, NOT missing characters/CER.
For each prediction matched to the TextRegion with greatest intersection,
measure area of other regions outside that primary region divided by crop area.
This is a diagnostic, not article truth. Exclude/count invalid source polygons
without repair. Assert union >= best-single coverage and bounded metrics.
Record model classes, image/source hashes, package versions, cold total and
per-forward latency. No threshold tuning or promotion based on this pilot.

Sources reread: DocLayout-YOLO arXiv:2410.12628v1 (2024-10-16), main text
sections 1–5.3; current official README and full yolov10/predict.py at
32a8ec276b3d79bf40561c4bc4b8e21ef32ac6fd. The code filters confidence and
rescales boxes to original image coordinates; its labels are document elements,
not guaranteed newspaper columns. Chronicling immutable dataset README confirms
LFS JPGs and split scheme. No claim to have read every appendix or newer paper.

All seven scientific gates remain false; strict/search_v1/lexical_alnum unchanged.
