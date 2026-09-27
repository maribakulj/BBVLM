# Blind OCR input comparison

Read only this file, task.json and the 32 PNGs listed there. Visually inspect
every target and context image. Do not read anything else in the repository,
other outputs, scripts, references, reports, XML or prior experiments.

For each ID, transcribe the TARGET passage only. Its matching CONTEXT image
shows the same passage with neighboring lines; use neighbors to disambiguate
but do not append their text. The target rectangular crop may contain slivers
of adjacent lines at its very edge: transcribe the central complete passage,
not these adjacent fragments. No colored marker is part of the source text.

Preserve printed spelling, capitalization, accents, apostrophes, punctuation,
explicit hyphens and visual line breaks. Never modernize, translate, expand
abbreviations or repair grammar. If a character is genuinely unreadable, make
the best diplomatic reading and mark the ID uncertain; never omit it.

Write sol.json with schema bbvlm.unmasked-a31/1, reader gpt-6-sol,
inspected_paths (all exact relative PNG paths), transcriptions (one text per
exact ID T001 through T016) and uncertain_ids. Use \n for visual line breaks.
No prior candidate or ground truth is available to you.
