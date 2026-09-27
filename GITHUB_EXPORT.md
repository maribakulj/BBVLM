# Research branch through A35

This branch imports the autonomous BBVLM work through A34 from checkpoint v27.
It retains the existing master history and files, and adds the experimental
code, tests, protocols, literature reviews, raw model responses and measurements.
The seven project completion gates remain false. A32 is experimental; A33 and
A34 punctuation rescue are rejected. These are research results, not a release.

Start with `experiments/loop/README.md`, `experiments/loop/CHECKPOINT.json`,
`experiments/loop/LITERATURE.md`, `experiments/loop/REFERENCE_AUDIT.md` and
`IMPLEMENTATION.md`. The latest report is
`experiments/loop/native-refinement-a35/RESULTS.md`.
A35 adds recognized-word geometry ablation, joint text/box metrics and a visual regression audit; no project completion gate is satisfied.

## Reproduction

Create a CPU virtual environment and install `requirements-experiment.txt`.
Run tests with `PYTHONPATH=src python -m pytest -q` (72 passed, 1 skipped in
the source workspace). Restore public assets using
`python scripts/restore_public_assets.py`, then use
`PYTHONPATH=src python scripts/autonomous_loop.py --execute` for ready phases.
Stored results cause completed phases to be skipped. Re-running an individual
experiment requires its public inputs and any earlier recognition cache named
by that experiment; consult its scripts and protocol before rerunning.

Large corpus images, weights, computed logits, runtime databases and redundant
console dumps are excluded from Git. `GITHUB_EXPORT_MANIFEST.json` records the original A34 import; subsequent commits carry their own diffs. It records
included and omitted checkpoint files with hashes. Three recent geometry audit
panels are retained for review. The full portable checkpoint v27 remains the
recovery copy for historical visual inputs and caches; its SHA-256 is
`6aeb2afa4c76f32c18c5bf23ec0f32edf32fa927c0d6a11abe614c3b17770482`.

The import preserves exact protocol, response and measurement bytes. Historical
absolute sandbox paths in provenance records are retained as evidence, not
rewritten into claims of portability. No reference annotation was replaced by
a prediction, and no rejected candidate was promoted.
