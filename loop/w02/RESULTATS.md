# W02 — résultats (coupure de mots choisie par Tesseract, bords à l'encre)

## 52 pages O07-O23
| mesure | sans W02 | W02 |
|---|---|---|
| CRITERE (C02b + S14) | 27 / 52 | **28 / 52** (BiedBern gagnée ; aucune page perdue) |
| somme txt+IoU80 | 43,947 | **44,025** |
| pages en recul txt+IoU80 > 0,01 | — | 14 (gains > 0,01 : 12) |

Par écriture (écriture déclarée par le lecteur) :
| | pages | Δ somme txt+IoU80 | gains > 0,01 | reculs > 0,01 | frontières ≤ 0,5c (CRITERE) |
|---|---|---|---|---|---|
| Fraktur | 31 | **+0,256** | 11 | 5 | 22 gains, 4 reculs |
| romain | 21 | **−0,178** | 1 | 9 | 0 gain, 13 reculs |

Reculs > 0,01 : albedm, culmsent, hackherz, heptaldai, chridiss, emmeprac, AyrmThes, buchdas, busmexpo, cingdei, ferrepit, abdipre, branchri, caladr (9 romain, 5 Fraktur). Examen : sur le romain, le modèle `lat` de Tesseract place ses coupures moins bien que notre DTW (coupures dans les ligatures et les abréviations) ; sur le Fraktur, gains nets (euanaua, brochrnx +0,049, dalarie +0,030, BiedBern 94,7 → 99,4 % ≤ 0,5c).

## Critère figé : tenu (CRITERE ne baisse pas, aucune page ne perd CRITERE, somme txt+IoU80 en hausse) → **W02 ADOPTÉE** (BBVLM_W02 = 1 par défaut), avec le recul sur le romain signalé.

## O24 (4 pages neuves Fraktur) — W02b (= W02 ici)
| page | ≤ 0,5c sans → W02 | txt+IoU80 sans → W02 | CRITERE |
|---|---|---|---|
| AusdeErb/13 | 95,9 → **100** | 0,731 → **0,772** | ✓ → ✓ |
| backhart/121 | 94,87 → 95,73 | 0,763 → 0,770 | ✗ → ✗ (1 ligne en échec) |
| buchdas/27 | 97,97 → **96,34** (pire 1,24 → 2,84c) | 0,803 → **0,782** | ✗ → ✗ |
| heptaldai/230 | 97,9 → 97,2 | 0,859 → 0,865 | ✓ → ✓ |
Somme des taux +2,6 pts, somme txt+IoU80 +0,033, mais buchdas recule de 0,021 > tolérance 0,01 → **W02b (critère plus strict, par page) non tenu**. buchdas est une Schwabacher du XVIe s. (ꝛ, abréviations) où le modèle Fraktur de Tesseract se trompe de coupure.

## Suite
W02c : W02 désactivée sur le romain (écriture déclarée), à valider sur des pages neuves en romain (le recul du romain est mesuré, mais la règle est réglée sur ces pages).
