# A56 — suitability audit of Europeana Historical Newspapers GT

## Frozen question

Can the 50-page Europeana Newspapers PAGE XML release (Zenodo 2583866) serve
as an independent ground truth for **word** and **line** geometry, rather than
only for region segmentation and text?

## Source and integrity

- record: <https://doi.org/10.5281/zenodo.2583866>
- archive: `gt_page.zip`
- expected size: 813.9 kB (Zenodo display)
- expected MD5: `02598a36eb09d50ccb6276f87d81be6c`
- immutable source archive is not committed; only its manifest and audit are.

## Predeclared audit

For every XML in the archive, count PAGE elements by local name, including
`TextRegion`, `TextLine`, `Word`, `Glyph`, `Baseline`, `Coords`, and
`TextEquiv`; record PAGE namespace, creator, timestamps, image dimensions,
and which hierarchy levels carry coordinates and Unicode.

The corpus qualifies for word-box validation only if all of the following are
documented by the release and present in the files:

1. word-level polygons or rectangles exist;
2. their provenance is manual or independently adjudicated (not merely an
   OCR engine export);
3. coordinate convention and annotation instructions are available;
4. images and XML are paired by stable identifiers.

Line validation requires manual/adjudicated line coordinates and convention
documentation. Region-only polygons remain useful for OLR, but cannot certify
word boxes. No image archive will be downloaded unless the XML granularity
passes the corresponding gate.

## Leakage and decision rule

This is a corpus-suitability audit, not a model score. It does not tune any
parameter and consumes no BBVLM test page. A failure is recorded as a useful
negative result. Predictions must never replace the released XML.
