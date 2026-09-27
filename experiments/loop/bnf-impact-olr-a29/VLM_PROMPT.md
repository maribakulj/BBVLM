# A29 blind visual reader instructions

Inspect only `public-task.json` and the eight JPEG files it names.  Do not open
the XML, ZIP, private map, scripts, reports, A27 material, or any other files.

Return strict JSON at the requested output path:

```json
{
  "schema": "bbvlm.bnf-impact-olr-a29-candidate/1",
  "reader": "gpt-6-luna",
  "roles": {"Q001": "BODY"},
  "streams": [{"region_tokens": ["Q001", "Q002"]}],
  "uncertain_tokens": []
}
```

Assign every token exactly one role from `TITLE`, `BODY`, `OTHER`.  Every token
with role TITLE or BODY must occur exactly once in `streams`; OTHER must not
occur there.  Order streams globally as they should be encountered on the page
and order tokens inside each stream.

A stream is a coherent editorial flow, not necessarily a single visual block:
it may cross columns and contain internal subheadings.  Use typography,
vertical continuity, column-bottom/top continuation, and visible subject
matter.  Prefer a conservative split when a join is genuinely ambiguous, but
do not systematically emit singleton streams: a frozen CPU step can merge only
adjacent small-gap fragments and cannot repair a wrong global order or a wrong
cross-column assignment.
