# A31 — user-requested blind Sol rerun without destructive crop annotations

27 September 2026. Reuse all sixteen consumed A30 targets. No error-selected
subset and no reference/prior-output access for the new gpt-6-sol reader.
One fresh high-reasoning subagent, 32 inspected images (target/context pairs),
same 1200px-minimum cubic resize as A30. Only the input preparation and target
designation change: no masking, no red overlay, 65px context above/below and
12px lateral extension beyond the old bbox in a separate image.

Primary comparison is normalized CER using the unchanged A30 audit function,
applied symmetrically to both model outputs and the unchanged distributed GT.
Strict NFC is secondary. This profile is NOT verified Gallica/Exalead behavior.
Never treat a posthoc re-score as fresh validation or replace GT with predictions.
Report improvements AND regressions and preserve all originals.

This jointly tests annotation removal plus context, not a factorial ablation.
One sample per condition cannot separate preparation effect from stochastic
variation. Parent visual review has seen alternatives; new subagent has not.
No claim of model-superiority or zero real OCR error from this experiment alone.

The A30 preparer actually whitened all pixels outside the polygon despite a
12px bbox margin and drew a red two-pixel contour on the boundary. Thus the old
margin was not genuine contextual information. This diagnosis is grounded in
the local preparer code and the original TIFF, not a new literature hypothesis.
