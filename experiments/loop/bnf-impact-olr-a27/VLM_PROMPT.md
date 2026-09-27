# Blind visual task A27

Inspect only the raw page preview, the six labelled vertical panels, and the
public task manifest supplied with this prompt. Do not open any XML, source ZIP,
mapping, evaluation code, prior report, or other experiment file.

Each opaque token denotes one polygonal text region. In a single visual pass:

1. assign every token exactly one role: `TITLE`, `BODY`, or `NON_ARTICLE`;
2. group content into coherent editorial reading streams;
3. list each stream's tokens in reading order.

`TITLE` includes titles and internal subheadings. `BODY` includes editorial
prose. `NON_ARTICLE` includes running headers, page furniture, and material that
is outside an editorial reading stream. Do not invent tokens. Every `TITLE` or
`BODY` token must occur exactly once in `streams`; `NON_ARTICLE` tokens must
occur in no stream. Preserve a stream when it continues at the top of the next
column. A title inside an existing stream does not necessarily start a new one.
These visual streams may correspond to articles or larger editorial units; do
not assume that every title starts a separate article.

Write JSON only to the requested output path with this schema:

```json
{
  "schema": "bbvlm.bnf-impact-olr-a27-prediction/1",
  "reader": "gpt-6-luna",
  "roles": {"TOKEN": "TITLE|BODY|NON_ARTICLE"},
  "streams": [
    {"stream_id": "S1", "region_tokens": ["TOKEN", "TOKEN"]}
  ],
  "uncertain_tokens": [],
  "notes": "brief visual-only caveats"
}
```

