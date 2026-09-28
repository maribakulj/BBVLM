# A57 — checkpoint extension-loss repaired

The legacy checkpoint builder silently replaced registered A54-A56 evidence and phase entries whenever checkpoint_bundle.py invoked it. Original reports survived. We reproduced the missing entries in the restored v41 checkpoint, recovered them by running their report-based registration scripts, and fixed the builder to preserve extension evidence/phase IDs. Built-in entries are still refreshed; completion of extra phases is recomputed from artifact presence; protocol completion gates stay authoritative.

One regression test covers two repeated saves, unique phase identity, unchanged extension evidence, missing-artifact invalidation, and refusal to inherit a stale true completion gate. The test passes. `autonomous_loop.py --execute` finds no unfinished registered CPU phase and runs no duplicate inference. All seven global completion gates remain false.

This is a resumption integrity fix, not an OCR/geometry improvement. It avoids losing the loop's latest findings on subsequent runs.
