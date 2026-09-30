# S14 — résultats (lettrine incluse dans la première ligne et le premier mot)

Détection seule sur les 52 pages : après les contraintes de forme, 5 déclenchements (euanaua, extraudeu : vraies lettrines ; hermhyst ×2 : notes de musique ; brochrnx : grand S Fraktur), les 3 faux positifs écartés par la condition « le mot lu commence par deux capitales ».

| page | CRITERE (lignes en échec) sans → S14 | txt+IoU80 | rappel de lignes (segeval) |
|---|---|---|---|
| euanaua/143 | 2 → **1** (✗ → ✗) | 0,859 → 0,859 | 0,909 → **0,955** |
| extraudeu/15 | 4 → **3** (✗ → ✗) | 0,897 → **0,903** | 0,810 → **0,857** |
| hermhyst/149 (faux positif écarté) | 2 → 2 | 0,536 → 0,536 | 0,778 → 0,778 |
| brochrnx/138 (faux positif écarté) | 2 → 2 | 0,865 → 0,865 | 1,000 → 1,000 |
| 48 autres pages | aucun déclenchement | — | — |

- Critère figé (aucun recul, au moins une ligne à lettrine au-dessus de l'IoU 0,5, faux déclenchements vérifiés à l'image) : **tenu → S14 ADOPTÉE**.
- Pas de page gagnée au CRITERE : euanaua garde un échec (« Am I. Sontag », titre dont la VT englobe la lettrine d'un autre paragraphe), extraudeu garde les lignes « mit bekannt gemacht » / « L. S. » (lecture antérieure à P6e).
- ALTO archivés régénérés : o*/alto/euanaua_842599541_00000143, extraudeu_630991022_00000015 (XSD valides).
