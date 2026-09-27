# A27 — blind one-pass visual stream grouping and OLR

## Question

Can one visual-language pass recover editorial reading-stream membership,
semantic region roles, and within-stream reading order from a historical French
newspaper page more accurately than geometry-only grouping, while reusing
external TextRegion polygons and preserving PAGE/METS-compatible identifiers?

## Reference and split

The source is the official BnF corrected-press IMPACT archive already hashed
in A26. The validation page is the second PAGE XML, lexicographically, in the
first filename-prefix group. Selection uses the central-directory manifest
only. The PAGE member and image must remain unopened until this protocol, the
preparer, evaluator, prompt, and split hashes are sealed.

The reference is conditional: source TextRegion polygons are treated as oracle
regions. Nested PAGE `OrderedGroup` members define ordered reading streams and
their `RegionRefIndexed@index` values define within-stream order. Direct members
of the outer `UnorderedGroup` are outside those streams. The PAGE files contain
no explicit article IDs, so this experiment does **not** treat an OrderedGroup
as proven article membership. It does not score word boxes or claim end-to-end
layout accuracy.

## Candidate input and leakage controls

After sealing, the preparer extracts only the chosen image and XML, then emits
a raw page preview plus six enlarged vertical panels. Every TextRegion polygon
is labelled with a deterministic opaque token unrelated to the native PAGE ID
or order. The reader receives only those images, the public token inventory,
and `VLM_PROMPT.md`; it must not inspect the XML, mapping, source archive,
reference types, transcriptions, or evaluator.

Exactly one primary visual reader is used (gpt-6-luna). Sol is permitted only
for a targeted adjudication after a documented structural failure, never as a
silent ensemble. The output is strict JSON: one role for every token and a list
of ordered editorial streams. No reference is used to repair the prediction.

## Metrics and gates

The evaluator fails closed if the reference has zero regions or zero ordered
streams. It reports:

- content eligibility precision/recall/F1;
- ordered-stream same-group pair precision/recall/F1;
- within-reference-stream pairwise order accuracy;
- exact token coverage and duplicate-token violations;
- optimistic geometry baseline using oracle PAGE heading/paragraph roles, to
  isolate the remaining grouping problem.

A27 is successful only if the one-pass VLM has exact token coverage, no
duplicate region assignment, eligibility F1 >= 0.98, stream-pair F1 >= 0.90,
within-stream order accuracy >= 0.98, and stream-pair F1 strictly exceeds the
optimistic geometry baseline. These are preregistered conditional gates; even
a pass does not establish article truth, perfect boxes, perfect OCR, or final
project success.

