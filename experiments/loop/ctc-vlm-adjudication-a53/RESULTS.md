# A53 — localized CTC/VLM adjudication improves aggregate CER but regresses exact lines

This is a consumed-data development diagnostic on the 15 A23 lines where the
cached Sol/VLM transcription and native PERO recognition disagree.  One blind
Luna pass inspected the crop plus randomly labelled alternatives; no layout or
recognizer was rerun.

## Result against the immutable SBB derivative

| output | strict CER | diplomatic CER | retrieval-fold CER | retrieval-exact lines |
|---|---:|---:|---:|---:|
| cached VLM/Sol | 11.480% (76) | 4.913% (34) | 2.757% (15) | 6/15 |
| cached PERO/CTC | 11.631% (77) | 4.624% (32) | 2.206% (12) | 8/15 |
| Luna adjudication | **10.574% (70)** | **3.902% (27)** | **1.471% (8)** | **9/15** |

Luna chose or produced a reference-best/tied line on 7/15 disagreements and
returned `NEITHER` five times.  The forced-CTC Viterbi margin alone identifies a
reference-best/tied option on only 8/13 scoreable lines.  It is therefore useful
as a contradiction/routing signal, not a safe automatic winner.

## Frozen gate

The aggregate non-inferiority condition passes, but the per-line protection
fails: Luna changes three lines for which one frozen candidate is exactly the
SBB derivative.  The complete development gate therefore **fails**.  A lower
mean CER is insufficient when producing validation-quality ALTO or ground truth.

The raw response also omitted the selected option text in ten A/B records.  It
is preserved unchanged.  Before any score succeeded, the same reader copied
the already-frozen selected strings into `luna-response-bound.json` without
reopening images or changing choices.  The report records this mechanical
transport repair; A53 is not a pristine validation.

## Decision

- Reject unconstrained visual A/B adjudication as an automatic overwrite.
- Retain PERO CTC as a cheap independent contradiction and word-alignment
  signal; do not treat its path score as truth.
- Retain the VLM pass for joint transcription, roles, relations, metadata and
  retrieval normalization, but route unresolved text disagreements to explicit
  review/abstention.
- Freeze any non-regression guard before a new dataset.  Do not tune it on these
  consumed lines.
- The targeted Sol rereading of the three apparent regressions is a post-score
  reference audit only and cannot rescue the A53 gate.

Cost: one Luna adjudication pass over 15 line crops; cached PERO logits and
texts; zero recognition/layout reruns.  The later Sol audit covers only three
flagged crops and is reported separately.

## Post-score Sol audit

The targeted image-only Sol rereading confirms that Luna dropped `t` in
`verſtehen` and in `ſextodecimo`, despite marking both choices certain. On the
third line Sol confirms the lexical content of the exact candidate but changes
spacing. This strengthens the rejection of uncertainty-only escalation and is
fully documented in `POST_SCORE_AUDIT.md`; because it was triggered by the
score, it does not alter the failed frozen gate.
