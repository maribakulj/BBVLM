# A53 — CTC/VLM disagreement adjudication

Frozen before reader inference on 2026-09-28.

## Hypothesis

A cheap CTC recognizer can expose visually unsupported VLM text without being
trusted as final OCR.  One Luna pass over only the 15 lines where cached A23
Sol/VLM text and native PERO text disagree will choose the visually supported
candidate, or transcribe `NEITHER`.  This should beat both complete candidates
without rerunning layout or recognition.

The design is motivated by Greif et al. (arXiv:2504.00414): image plus an
independent conventional OCR candidate improves multimodal post-correction,
whereas asking an mLLM to revise its own prior transcription did not materially
help.  It also follows OCR-EDR's principle that correction should be triggered
by a localized image/text mismatch rather than by unconstrained rewriting.

## Frozen inputs and blindness

- A23's 16 already-consumed oracle line crops, Sol transcriptions and cached
  PERO logits/native text.  The one exact-agreement line is not sent.
- Candidate provenance is randomized with seed `2026092801`.
- The reader sees only each crop and candidates A/B.  It never receives the
  SBB reference, CTC score, provenance, prior CER or expected answer.
- This is development evidence only: the lines were consumed in A22/A23 and
  cannot open any project completion gate.

## Reader and output contract

One `gpt-6-luna` reader inspects all 15 images at original resolution and emits
exactly one record per ID: `choice` in `A|B|NEITHER`, `text`, `uncertain`, and a
short glyph-grounded reason.  No automatic Sol escalation.  The evaluator
rejects missing/duplicate IDs and any A/B record whose text differs from the
selected frozen option.

## Measures and frozen decision

- strict NFC CER and retrieval-fold CER for native CTC, VLM, adjudicated output;
- per-line non-regression against the better complete candidate;
- selection accuracy against the immutable SBB derivative;
- number of images sent, passes and cached CPU cost;
- diagnostic relation between forced-CTC path margin and reference winner.

Pass as a *development candidate* only if adjudication strict CER is no worse
than `min(CER(VLM), CER(CTC))` and no line exact under both candidates becomes
worse.  Zero against this derivative would still not certify truth.
