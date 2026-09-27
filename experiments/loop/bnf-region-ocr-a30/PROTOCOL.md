# A30 — blind frontier OCR on unopened French BnF regions

## Question

Can one frontier VLM pass transcribe historical French newspaper region crops
at zero character error against the independent manually transcribed BnF IMPACT
PAGE text, without seeing XML, references, layout IDs, or prior predictions?

## Frozen selection

The validation source is the second PAGE XML in the second filename-prefix
group (`00123532`), selected from the central-directory manifest only.  This is
a different number from the A27/A29 pages.  Protocol, prompt, preparer,
evaluator and metric implementation are hashed before opening.

After opening, the preparer deterministically selects 16 non-empty `paragraph`
or `heading` TextRegions with 40–400 NFC reference characters and bounding box
at least 180×35 pixels.  Candidates are ordered by SHA-256 of a sealed seed plus
native region ID, never by OCR disagreement.  Each polygon is cropped from the
source TIFF with 12 pixels context, masked white outside the polygon, and
upscaled only when narrower than 1200 pixels.  Opaque IDs are shuffled and the
private source-ID/text mapping is denied to the reader.

Luna is the only primary reader.  Sol is allowed only as a separately labelled
blind escalation after measured non-zero CER; it cannot replace the independent
primary result.

## Transcription and metrics

The reader must reproduce printed spelling, case, accents, punctuation,
hyphenation and line breaks; no modernization or silent completion.  The
strict view applies NFC, CRLF→LF, strips outer blank lines and trailing spaces
per line.  The search view applies NFKC, lowercase, joins printed end-of-line
hyphenation, maps typographic apostrophes to ASCII and collapses whitespace.

The preregistered OCR gate requires exact ID coverage, declared inspection of
all 16 images, strict CER exactly 0, and 16/16 exact strict regions.  Search CER
is reported but cannot satisfy the zero-CER claim.  Even a pass would validate
only region-crop transcription, not page coverage, reading order, word boxes,
article truth, or perfect ground truth.
