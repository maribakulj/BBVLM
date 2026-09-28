# Claude competing-branch audit

Inspected on 2026-09-28 before interpreting A51 and before selecting the next
hypothesis.

- Repository: `maribakulj/BBVLM`
- Branch: `claude/astra-branch-analysis-wf4gj4`
- Merge base with Codex branch: `60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`
- State at inspection: two commits ahead of `master`, two commits diverged from
  `codex/autonomous-research-a34`.

## Material inspected

`loop/ETAT.md`, `JOURNAL.md`, `LITTERATURE.md`, O01 protocol/results, O02
protocol, and the CER/convention scripts.

## Findings that affect BBVLM

1. O01 provides a useful counterexample to “zero CER against GT equals perfect
   reading”: Opus had one reference disagreement, adjudicated visually as a
   reference error, and therefore zero reading errors but non-zero raw CER.
2. On that single page, a reduced whole-page view beat page plus full-resolution
   bands. Resolution/cropping must be tested, not assumed.
3. The scorer separates strict, diplomatic and normalized text and does not mix
   reading order into CER. This agrees with BBVLM's layered evaluation policy.
4. The O01 evidence is one clean 27-line page. It cannot establish a system-wide
   0% CER; O02 has a frozen four-page protocol but no result at inspection time.
5. Claude's files live under `loop/` and do not overlap the Codex
   `experiments/loop/` implementation. No merge or overwrite is needed.

## Policy from this point

At the start of every new experimental hypothesis, compare the Claude branch
head to the last recorded head, read its new protocols/results/code, and record
what was reused or rejected. Never merge scores or call one branch's consumed
pages independent evidence for the other.
