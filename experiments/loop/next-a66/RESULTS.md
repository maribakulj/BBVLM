# A66 — real DocLayout-YOLO inference, 2026-09-28

Five purposively selected official Chronicling Validation pages; 1,317 valid
TextLine polygons, two invalid lines excluded without repair. Ten real model
forwards, no OCR/VLM. Images and XML hashes verified; image dimensions matched.
All predictions were persisted before XML geometry was read. Test pages opened:0.

| Resolution / policy | Boxes | Union below 50% | Single box below 95% | Fragmented | Crops >1% foreign area |
|---|---:|---:|---:|---:|---:|
| 1024 all |174|8|133|64|12|
| 1024 text-like |168|8|133|64|12|
| 1600 all |186|10|142|72|13|
| 1600 text-like |180|10|142|71|13|

Positive: generic image-only regions cover most annotated lines on this small
transfer sample. Negative: raising resolution does not uniformly improve coverage;
Berliner misses increase2→7 while Bonner misses decrease6→3. More than half the
incomplete-single-box cases are NOT necessarily true clipping: fragmentation and
annotation conventions require visual checking before attributing missing glyphs.
Neither resolution is promoted as a final winner. No PERO superiority or perfect
word boxes demonstrated. Crops are document-element regions, not guaranteed columns.

Inference wall time including model initialization:16.0506s; full score29.3664s.
Individual calls0.75–2.68s CPU, four threads. DocLayout-YOLO0.0.4,
torch2.14.0+cpu, torchvision0.29.0+cpu, numpy1.26.4, Shapely2.1.2.
Model weights40,709,302bytes (verified existing manifest). CPU environment reused
cached wheels; no GPU/cloud purchase. Dependencies deliberately use headless
OpenCV4.8.1.78; training-only albumentations absent. Monetary runtime cost is not
exposed, not asserted zero.

Operational negatives preserved: initial asset loader assumed all JPGs were LFS
pointers and failed on a direct Git JPG. Retry verifies Git blob content, then LFS
SHA when relevant. Initial queue resource typo rejected before work. A reference
addendum accidentally touched an immutable A63 input, correctly marking descendants
stale; original bytes restored, addendum moved, all prior fingerprints and outputs
revalidated without inference rerun. Recovery receipt is in queue-state.json.

Source reviews and three separate paper summaries are in PAPER_SUMMARIES.md.
Chronicling lines remain selectively corrected, not perfect geometric truth.
All scientific gates remain false. Next: image-grounded audit of fragmentation
before choosing a crop repair; preserve 100 Test pages and frozen OCR normalizations.
Original branch only, never merge or update master/main.
