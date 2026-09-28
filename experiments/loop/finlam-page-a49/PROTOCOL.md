# A49 — unopened validation of recurrent columns

Six new Finlam test rows were selected by hash before any row content or image
was opened.  A48 is development-only and excluded.  The recurrent-column
algorithm and every numeric parameter are frozen in `split.json`.

Evaluation uses the same oracle zone polygons/classes for both legacy and
candidate, so it isolates column/order/article reasoning and does not claim
end-to-end detection.  Report global pair order, within-article order, and
same-article pair F1.  All denominators include misses.  Finlam issue-logical
order may place continuations before page-local material; report this separately
and do not silently redefine it as visual order.  No VLM sees A49 unless the CPU
candidate fails a predeclared gate; any escalation is a new blind experiment.
