# A29 — one-pass visual OLR plus frozen CPU continuation merge

## Question

Can a single blind Luna visual pass produce conservative semantic reading
streams whose residual over-segmentation is closed by a frozen, cheap CPU rule,
on a BnF page not used to develop the rule?

## Development and frozen rule

A27 is development only.  Sol's 34 streams never crossed a PAGE OrderedGroup,
but split six large reference groups.  Consecutive fragments from the same
reference group had a maximum vertical gap of 19 pixels; true boundaries had a
minimum gap of 35 pixels.  Before selecting or opening A29, the merger was fixed
to join only consecutive VLM streams whose endpoint boxes overlap horizontally
by at least 0.60 and whose vertical gap is at most 0.007 times page width.  It
never changes token order or invents a non-adjacent link.

This operationalizes the visual-distance rules used in newspaper article
reconstruction literature and keeps the semantic decision in one VLM pass.  It
is not an Eynollah replacement: Eynollah remains a candidate region/line/order
stage, while this rule targets the measured semantic fragmentation after the
VLM.

## Independent validation

The validation page is the third PAGE XML lexicographically in the first BnF
filename-prefix group (`00123453`).  Selection uses only the already published
central-directory manifest.  The protocol, prompt, preparer, evaluator, merger,
and their hashes are sealed before opening the image or XML.

The reader receives only a raw page, an opaque-ID labelled page, six enlarged
vertical panels, and the token inventory.  It is denied the ZIP, XML, ID map,
reference order, evaluator, A27 predictions, and development report.  Luna is
the sole primary reader.  Sol is allowed only after a documented structural
failure.

The reference is conditional on oracle BnF TextRegion polygons.  PAGE
OrderedGroups are scored as ordered streams but are not claimed to be explicit
article truth.

## Gates

The evaluator fails closed on empty reference streams.  Both raw and merged
predictions are reported.  The conditional gate requires exact role/token
coverage, eligibility F1 >= 0.98, merged stream-pair F1 >= 0.90, merged
end-to-end order-pair recall >= 0.90, and a strict improvement over both raw VLM
streams and the optimistic geometry baseline.  Passing would still not certify
end-to-end regions, article truth, OCR, or final project success.
