# A26 structural failure — 2026-09-27

The BnF IMPACT archive is an official French press ground-truth source, but
the four sealed PAGE 2010 files contain **TextRegion** polygons and region
transcriptions only. They contain zero `TextLine`, `Word`, or `Glyph`
elements. Consequently A26 has zero word references and cannot measure word
boxes, OCR CER on words, or superiority over PERO.

The sealed A26 evaluator computed a vacuous boolean gate on empty collections.
That boolean is rejected. `output/report.json` is retained as negative
evidence, not as a successful score. Future evaluators must fail closed when
the number of reference pages, groups, lines, or words required by their
contract is zero.

The same files do contain useful manually produced evidence for a different
task: nested PAGE `OrderedGroup` elements define groups of TextRegions and their
order. They are not explicit article IDs. A26 pages are consumed development
material for that task. A27 uses an unopened page and a separately frozen
protocol to test one-pass visual stream grouping and reading order.
