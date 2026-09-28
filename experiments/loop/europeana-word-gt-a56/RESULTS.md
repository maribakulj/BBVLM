# A56 — result: useful region/OLR reference, no word or line geometry

## Decision

The Europeana Newspapers release at Zenodo 2583866 is **rejected as a word-box
or line-box ground truth** for BBVLM. It remains a potentially useful independent
50-page reference for region polygons and region reading order.

The audit parsed every XML from the checksum-verified archive. It did not infer
granularity from the record title or from token counts.

| item | result |
|---|---:|
| PAGE XML files | 50 |
| `TextRegion` | 2,458 (present on 50/50 pages) |
| `TextLine` | 0 |
| `Word` | 0 |
| `Glyph` | 0 |
| `SeparatorRegion` | 678 |
| indexed region-order references | 2,242 |
| XML creator | `FineReader Engine 10` on 50/50 pages |

The source archive is 813,883 bytes, MD5
`02598a36eb09d50ccb6276f87d81be6c` (matching Zenodo), SHA-256
`bdcc267a2839cd91419b68f69c6f460416999c604312c092a2ca109af476fed2`.

## Interpretation

Each text region has a polygon and region-level `TextEquiv`; the files also
carry explicit region ordering. But PAGE XML's ability to encode words does not
mean this release contains them. Deriving words from the region transcript or
from FineReader output would create pseudo-ground-truth and would make any
word-box score circular.

The Zenodo record describes the pack as 50 pages for OCR/OLR and separately
publishes FineReader 11 outputs, but does not document manual/adjudicated word
or line coordinates. The XML producer is FineReader Engine 10. These facts are
not evidence that the region polygons themselves are unfit; they are decisive
against promoting absent word/line annotations to perfect geometry.

## Cost and leakage

- downloaded: only the 813.9 kB XML archive; the 31 MB images were not needed;
- CPU: one deterministic parse of 50 XML files;
- OCR/VLM/layout passes: 0;
- test pages consumed by BBVLM: 0;
- original files changed: 0.

## Consequence

Keep this pack on the OLR candidate list after verifying its region-annotation
provenance. For word geometry, continue to a corpus whose released files contain
manual/adjudicated word coordinates. For line/region geometry, Chronicling
Germany is a stronger next candidate because its paper explicitly separates
expert region polygons from automatically generated, selectively corrected
lines; that distinction must remain visible in the scorer.
