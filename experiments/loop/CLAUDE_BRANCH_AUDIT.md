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


## A59–A60
A59 : comparaison 33 ahead/10 behind. A60 : JOURNAL relu jusqu’à I01, SHA ba685e9b4c870e245d1d201381986178660abb4c inchangé. P7 rejeté et I01 motivent la comparaison pixels source/bandes ; aucun résultat indépendant emprunté.


## A61 — 2026-09-28
Relu JOURNAL I01 avant nouvelle hypothèse ; même SHA ba685e9b4c870e245d1d201381986178660abb4c. Aucun nouveau résultat adopté depuis A60.


## A62 — 2026-09-28
Relu JOURNAL I01, SHA ba685e9b4c870e245d1d201381986178660abb4c inchangé. Mise à niveau de l’orchestrateur, aucun résultat concurrent fusionné.

## A63 — 2026-09-28
Head76056c5c1957e0de4232f0aef1f6cbc7f2893402 et JOURNAL I01 inchangés. Code loop/outils/inflexion.py lu (blob6a374eb53f4ff31e475b49f50bfacdc90b1a38dd) : ciblage utile, lexique/majorité des marques u non transposable directement à0455. Aucun merge.

## A64 — 2026-09-28
Avant l'hypothèse, head
`76056c5c1957e0de4232f0aef1f6cbc7f2893402` et blob JOURNAL I01
`ba685e9b4c870e245d1d201381986178660abb4c` inchangés depuis A63. Aucun nouveau
résultat, protocole ou code concurrent n'a été adopté ou fusionné. A64 porte sur
une métrique officielle et non sur la règle d'inflexion I01.

## A65 — 2026-09-28
Référence distante relue : head76056c5c1957e0de4232f0aef1f6cbc7f2893402
inchangé. Aucun nouveau commit à examiner. Aucun code fusionné. Branche
principale master toujours60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec ; main absent.
Toutes les écritures de cette boucle visent codex/autonomous-research-a34,
sans force et avec un seul parent (pas de merge).

## A66 — 2026-09-28
Claude head rechecked76056c5c1957e0de4232f0aef1f6cbc7f2893402, unchanged.
Master rechecked after the actual experiment:60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec,
unchanged. A65 was pushed4706e6dab32207d4926c0c35dd37a093212b6c43 on the original
Codex branch. No merge, no force, no main/master update.

## A67 — 2026-09-28
Rechecked Claude76056c5c1957e0de4232f0aef1f6cbc7f2893402 unchanged before audit.
A66 parent53aea20cd5a0bd4f0bb8a5ad012647c3b54cd051 confirmed on original
codex/autonomous-research-a34. No Claude code imported; no main/master mutation.

## A68 — 2026-09-28
Avant de figer la règle de bord, références relues : Claude
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`, Codex
`b2d7d65a6914597a9d27d84e5c0d5b69d3a2eb4b`, master
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Claude est inchangé depuis A67 ;
aucun nouveau protocole, résultat ou code à importer. Aucun merge, aucune
écriture sur master/main, aucun force-push.

## A69 — 2026-09-28
Avant le transfert, Claude a été recontrôlé à
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`, inchangé depuis A68. La branche
Codex était `42e8c5ef6d3447d14522fd94d57179253e122dca` et master restait
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun fichier concurrent n'a été
fusionné ou copié. A69 reste sur `codex/autonomous-research-a34`, sans force.

## A70 — 2026-09-28
Claude est toujours à `76056c5c1957e0de4232f0aef1f6cbc7f2893402` ; Codex
était à `e76a6453859b1bd5462d7abe036e62ab48eadea2` et master à
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun changement concurrent,
aucun merge, aucune écriture hors `codex/autonomous-research-a34`.

## A71 — 2026-09-28
Avant l'audit visuel, Claude a été recontrôlé à
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`, inchangé. Codex était à
`80d1c7ebb4ffa2a10f09b57e363ba8c9282b136c` et master à
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun fichier concurrent importé,
aucun merge, aucune écriture sur master/main et aucun force-push.

## A72 — 2026-09-28
Avant l'hypothèse Eynollah ciblée, Claude était encore à
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`, inchangé. Le parent Codex était
`d6fa389b6e4a2c26b5e3e1518cd9e565a60e8029` et master restait
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun code concurrent importé,
aucun merge et aucune écriture hors `codex/autonomous-research-a34`.

## A73 — 2026-09-28
Après A72 et avant de définir son routeur, Claude a été recontrôlé au même head
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`. Il n'y a donc aucune nouveauté à
examiner ou réutiliser. Master est toujours
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`; aucun merge/main.

## A74 — 2026-09-28
Avant de figer le transfert, Claude a été recontrôlé à
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`, toujours inchangé. La branche
Codex était à `9d36ff79db7f25546b34f17378bd1d6603d6e8f3` et master restait
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun code concurrent importé,
aucun merge, aucune écriture sur main/master et aucun force-push.
