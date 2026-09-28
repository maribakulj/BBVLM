# A53 post-score visual audit

This audit was commissioned only after the A53 scores exposed three line-level
regressions. It is therefore diagnostic, not independent validation, and cannot
repair the frozen A53 gate. Sol received only the three images and opaque IDs;
it did not receive references, alternatives, CTC scores or Luna decisions.

| ID | frozen exact candidate | Luna A53 | Sol image-only rereading | finding |
|---|---|---|---|---|
| `R2922cb1c4d` | `bb. Et eſt acatalectus.` | `bb. Et eſt acatalectus .` plus an extra spacing error | `bb.Et eſt acatalectus .` | lexical content agrees with the exact VLM candidate/reference; spacing remains inconsistent |
| `R89b9dcb991` | `verſtehen gab. Aber die Dame hatte ſich damit` | `verſehen ...` | `verſtehen gab. Aber die Dame hatte ſich damit` | Sol and direct pixel inspection confirm the missing `t`; Luna is wrong |
| `Rf190cd318e` | `Anno ſupra ſeſquimilleſ. ſextodecimo.` | `... ſexodecimo.` | `Anno ſupra ſeſquimilleſ. ſextodecimo.` | Sol and direct pixel inspection confirm `ſextodecimo`; Luna is wrong |

The raw Sol JSON is preserved as `sol-postscore-audit.json`. The two clear
failures were confident Luna choices, so an uncertainty-only escalation policy
would not catch them. The safe conclusion is narrower: cached CTC disagreement
is useful for routing and can expose VLM errors, but neither the CTC score nor a
single visual adjudicator is a truth oracle. Automatic overwrite remains
rejected; exact candidate preservation or abstention must be frozen before any
new independent test.
