# A57 — durable resumption integrity

Observed: checkpoint_bundle.py invokes autonomous_loop.py, whose checkpoint() replaces the whole state from a phase list ending at A51. A54-A56 raw results survive, but registered evidence and phases disappear.

Freeze before repair: preserve extension evidence/phase records while regenerating legacy entries; recompute phase completion from artifact presence; never promote completion gates from prior state; preserve research notes without duplicate growth. Restore A54-A56 evidence from original reports, never from recalled scores.

Tests: reproduce extension loss before repair; test a synthetic extra phase through two checkpoint calls; delete its artifact and require complete=false; stale success flag must not override protocol. Execute ready phases once under the existing lock, bundle, inspect the archived state, verify source hashes. No OCR/VLM score claim.
