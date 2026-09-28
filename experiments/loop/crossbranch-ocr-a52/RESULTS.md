# A52 — same source/views expose a model-prior gap

This development replication is complete. It does **not** open a project gate:
both pages had already been consumed by Claude O02 and Claude's adjudications
are model-derived rather than independent human truth.

## Measured result against Claude's adjudicated derivative

| Page / reader | diplomatic CER | search_v1 CER | retrieval_fold_v1 CER |
|---|---:|---:|---:|
| P01 Roman — Luna | 0.272% (3) | 0.339% (3) | **0.000% (0)** |
| P01 Roman — Opus O02 | **0.000% (0)** | **0.000% (0)** | **0.000% (0)** |
| P01 Roman — Luna + targeted Sol | 0.453% (5) | 0.226% (2) | **0.000% (0)** |
| P02 Fraktur — Luna | 7.151% (65) | 5.186% (39) | 4.787% (36) |
| P02 Fraktur — Opus O02 A1 | 3.410% (31) | 1.862% (14) | 1.729% (13) |
| P02 Fraktur — Opus O02 A2 | **2.970% (27)** | **1.463% (11)** | **1.330% (10)** |
| P02 Fraktur — Luna + Sol rescue | 4.070% (37) | 2.261% (17) | 1.862% (14) |

`search_v1` ignores punctuation, whitespace, case and hyphen characters but
keeps accents. `retrieval_fold_v1` also strips diacritics and is an operational
retrieval equivalence only; it is never substituted for diplomatic truth.

## What prevented zero

On P01, Luna wrote `préfèrent`, `goûter`, `lumières`; direct visual inspection
shows the print has `préferent`, `gouter`, `lumieres`. These are three
language-prior modernizations, not reference mistakes. Sol corrected only the
third and independently repeated the first two. Thus Luna and Sol both reach
the user's accent-insensitive retrieval target of 0% but not diplomatic 0%; a
second frontier pass is not a reliable diplomatic repair.

On P02, Luna produced many plausible modernizations/substitutions, including
`vornemen→vernehmen`, `vornewret→vernewert`, `mãcherley→mächerlich`, and
`wort→wer`. Sol reduces the retrieval-fold edit count from 36 to 14, but Opus
A2 remains better at 10. Errors include `J/I`, `jmmer/immer`, `endtlich/endlich`,
abbreviation/diacritic readings and lexical replacements. Visual inspection
also finds one probable reference problem: the lower-right catchword visibly
reads `werck`, whereas the adjudicated derivative says `wort`. It remains a
flag; the immutable source is not changed or silently rescored.

## Why Opus beat Luna/Sol here

The source TIFFs, 1350-pixel page overview, 600-pixel bands and 120-pixel
overlap match Claude's preparation code. A52 additionally supplies half-band
×1.6 views. The readers received the diplomatic convention explicitly and no
reference alternatives. More resolution/context therefore does not explain
the remaining gap: on these pages the dominant variable is model-specific
resistance to linguistic modernization. The extra Sol pass helps hard Fraktur
but is still worse than the better Opus read, and it slightly worsens P01's
diplomatic score.

## Decision

- Keep Luna as the cheap semantic/metadata reader, not as the sole diplomatic
  transcriber for early print.
- Do not automatically escalate every page to Sol: it failed to remove the
  P01 bias and did not match Opus on P02.
- A future paid frontier OCR route must be triggered by deterministic
  uncertainty and evaluated on a new independently adjudicated set. Where
  available, Opus-like performance is a meaningful OCR comparator, not a truth
  source.
- Preserve two outputs: immutable diplomatic transcription and a derived
  retrieval-fold key. The 0% P01 retrieval CER is real under the declared fold;
  it must not be advertised as 0% diplomatic CER.

Cost: one Luna page-pair pass (29 image views) plus one post-failure Sol pass
(29 views; P01 restricted to three lines, P02 full page). No recognizer or
layout model was rerun.
