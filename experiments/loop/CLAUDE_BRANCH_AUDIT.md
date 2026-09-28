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

## A57 reinspection — 2026-09-28

Claude branch: 33 commits ahead / 9 behind our A56 head 2e3c0d7. Read current JOURNAL lines 180 onward and LITTERATURE L09-L10. S03 XY-cut improves the table-page joint text+IoU80 .062→.136, unchanged on other 19 development pages. S04 font-height correction helps EXTRACT alignment but has only development evidence. B01 center normalization worsens straight pages, so not adopted. P7 shape declaration failed; I01 targeted full-resolution diacritic arbitration reduces 147→129 edits across 16 consumed pages with no regression, awaiting O13. Reuse selective high-resolution evidence as a candidate, not a validated universal glyph rule. S05 text-anchor alignment is motivated by Feng/Manmatha and Yalniz/Manmatha; no independent result read yet. No competing-branch files merged.

A56 reinspection (recovered from tool log): 25 ahead / 8 behind; O11 edits 0,4,6,43, last dominated by one visual line split semantically by reference. S03/B01 result paths were then absent. This entry repairs an earlier documentation write that had not persisted.

## A58 — 2026-09-28
JOURNAL.md relu lignes210–257 SHA ba685e9b4c870e245d1d201381986178660abb4c ; comparaison 33 ahead/10 behind depuis f70b292. Aucun changement depuis A57 : I01 reste développé sur pages consommées, O13 attendu.

