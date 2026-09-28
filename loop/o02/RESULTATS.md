# O02 — résultats

CER diplo après `ocrd2.py` (espaces avant ponctuation retirées, règle OCR-D),
contre la référence distribuée puis contre la **référence adjugée** (arbitres
Opus distincts, aveugles X/Y, 86 lignes, `adjudication/`).

| page | lecture | distribuée | **adjugée** | lignes exactes | réf. fausse (car.) |
|---|---|---|---|---|---|
| borrdisc 19 (romain fr.) | A1 page | 0,090 % | **0,000 %** | 28/28 | 1 |
| | A2 page | 0,090 % | **0,000 %** | 28/28 | |
| actevedef 24 (Fraktur dense, 4643 car.) | B page+bandes | 0,409 % | **0,215 %** | 66/68 | 9 |
| | A2 page | 0,754 % | 0,582 % | 53/68 | |
| | A1 page | 2,283 % | 2,112 % | 33/68 | |
| goskeinf 32 (Fraktur) | A1 page | 1,050 % | **0,494 %** | 29/33 | 9 |
| | B page+bandes | 1,606 % | 1,235 % | 29/33 | |
| | A2 page | 2,162 % | 1,668 % | 27/33 | |
| drabnota 389 (Fraktur XVIe) | A1 page | 3,497 % | 2,750 % | 18/29 | 7 |
| | A2 page | 2,404 % | 2,970 % | 15/29 | |

Consensus (médoïde, vote ROVER simplifié, `outils/consensus.py`) des trois
lectures : actevedef 0,452 %, goskeinf 1,421 % — **pire que la meilleure
lecture seule**. Les erreurs d'un même modèle sont corrélées : la multiplication
des passes n'est pas la voie. Résultat négatif, retenu.

## Nature des fautes restantes (meilleure lecture par page)

- actevedef B : **1 vraie faute** (une espace) ; le reste est le titre courant
  « 20 ( o) » dont la référence ne garde que « 20 » (ornement).
- goskeinf A1 : 4 fautes lexicales sur zones abîmées (few/feuer, gedult/geduld,
  Zeenklappern/Zeneklappern, n̄/ñ).
- drabnota A1 : e suscrit lu tréma (4), J lu I (2), ã lu ä, folio et signature
  groupés avec d'autres lignes.
- A1 page seule sur actevedef : e suscrit systématiquement lu tréma (résolution
  insuffisante sur une page 2463×4060 réduite) ; les bandes corrigent cela.

## Ce que ça établit

- Deux pages en romain : **0 faute** (4 lectures sur 4).
- Fraktur : 0,2 à 3 % ; la résolution et la convention (e suscrit, I/J, lignes
  de folio/signature) dominent, pas la reconnaissance des mots.
- Les références distribuées ont 1 à 9 caractères faux par page : l'adjudication
  est indispensable pour mesurer 0 %.
- Limite : arbitres de la même famille de modèle que les lecteurs, sans
  agrandissement supplémentaire (pas d'outil d'image dans leur bac à sable).
