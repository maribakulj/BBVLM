# A30 blind diplomatic OCR

Read only `public-task.json` and every PNG path listed there.  Do not open XML,
ZIP, private maps, scripts, reports, other experiments, or any reference text.
Actually inspect all 16 images.

Return strict JSON at the requested output path:

```json
{
  "schema": "bbvlm.bnf-region-ocr-a30-candidate/1",
  "reader": "gpt-6-luna",
  "inspected_paths": ["exact/path.png"],
  "transcriptions": {"T001": "exact printed text"},
  "uncertain_ids": []
}
```

Cover every opaque ID exactly once.  Preserve printed spelling, capitalization,
accents, apostrophes, punctuation, explicit hyphens and visual line breaks.
Never modernize, translate, expand abbreviations, repair grammar, or add text
outside the red crop polygon.  Use `\n` between visual lines and no Markdown.
If a character is genuinely unreadable, make the best diplomatic reading and
list the ID in `uncertain_ids`; never omit it.
