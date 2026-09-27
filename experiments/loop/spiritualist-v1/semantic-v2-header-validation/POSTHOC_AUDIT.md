# A06 post-score convention audit — page 0029

This audit was written only after the frozen evaluation. It does not alter the
response, reference, thresholds or failed gate, and it is not an independent
adjudication.

Five of the ten role disagreements are a systematic vocabulary mismatch. The
reader assigns `ADVERT` to E9/Q8 (the boxed *Charges for Advertisements* block)
and P8/Z4/C9 (the boxed *Wanted a Ghost* block). The distributed annotations
encode those same regions only as physical `HEADER`/`TEXT` and include them in
reading order. The model's editorial interpretation is visually plausible, but
it cannot be counted as correct without a separately fixed annotation policy.

The remaining disagreements also expose different granularities: N6 and Z6 are
small date/page fragments grouped into the distributed masthead; A6 is a
mid-page ornamental heading called `MASTHEAD` by the reader but `HEADER` by the
source; H6 is a dateline-like header fragment called `OTHER`; and R7 is a
bottom-right note called `TEXT` rather than source `OTHER`.

Consequences for the next untouched page:

1. Separate physical role (`HEADER`, `TEXT`, marginal fragment) from editorial
   genre (`ARTICLE`, `ADVERT`, notice, masthead) instead of forcing one label.
2. Ask stream membership explicitly for every class. Advertising may be a
   separate readable unit and must not be silently discarded from ALTO/METS or
   retrieval even when excluded from a news-article stream.
3. Freeze a source-to-profile mapping before inference. The source labels are
   provisional physical annotations, not an adjudicated editorial taxonomy.
4. Do not rescore page 0029 under the revised convention; it is consumed.
