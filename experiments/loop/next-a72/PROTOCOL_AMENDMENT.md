# A72 backend amendment before scientific output

The frozen pages, resize, tiles, class, overlap threshold and local gate in
`PROTOCOL.md` are unchanged. The ONNX Runtime process attempted an unnecessary
external telemetry connection before producing any mask; the execution policy
stopped it. A second telemetry-disabled attempt was also stopped, so ONNX
Runtime is rejected for this experiment and no partial output is scored.

The retry uses the matching public native SavedModel directory
`modelens_textline_0_1__2_4_16092024` from Eynollah's official 0.9.1 training
layout archive. It is loaded through `tf.saved_model.load` under
`tensorflow-cpu==2.16.2`; only the `serving_default` signature
`[N,672,672,3] -> [N,672,672,3]` is called. All six model files are checked by
SHA-256 before inference. This is a backend substitution made before observing
any scientific result, not a parameter search.

The full Eynollah pipeline remains out of scope: no page, region, OCR, reading
order, or export stage is installed or run.
