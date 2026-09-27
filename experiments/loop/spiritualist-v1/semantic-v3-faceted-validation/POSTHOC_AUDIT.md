# A07 post-score audit — page 0039

This audit was written after the frozen evaluation. It does not alter the raw
response, reference, gates or failed result, and page 0039 is not reusable as an
independent validation page.

The faceted contract fixes the A06 deletion failure: all 21 reference stream
regions are retained, with no contamination, and the frozen column order gets
210/210 reference pairs. Editorial genre never controls inclusion. Luna proposes
21 `ARTICLE` regions and three `MASTHEAD` regions; these genres remain unscored
proposals because the corpus has no editorial-genre reference.

The failure moves to the fine physical distinction. Luna gets 15/24 physical
roles: five source `HEADER` regions become `TEXT`, three source `TEXT` regions
become `HEADER`, and one tiny `UNKNOWN` fragment becomes `HEADER`. Consequently
the CPU rule predicts the correct count of nine units but places several
boundaries incorrectly (pair precision 0.565, recall 0.619, F1 0.591).

Geometry after score shows why a cheaper router is plausible but does not prove
it. On 0039, source headers have heights 35–66 px and source text blocks
111–2348 px. On the four development pages, headers span 32–110 px and text
64–3133 px, so there is some overlap. A development-only calibration selects a
height/page-height threshold of 0.020, reaching macro SSU pair F1 0.969 and
HEADER/TEXT accuracy 0.902 with oracle coarse stream membership. It must be
tested on 0044 or 0050, never retrospectively promoted from page 0039.
