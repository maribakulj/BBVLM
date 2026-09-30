# W02d — résultats (25 pages en romain, O07-O25, développement)

| | sans W02 (W02c, état actuel) | W02 avec `script/Latin` |
|---|---|---|
| somme txt+IoU80 | **21,069** | 21,009 |
| pages en gain > 0,01 | — | 2 (AmmoLIBR +0,044, AyrmThes +0,012) |
| pages en recul > 0,01 | — | 6 (abdipre −0,024, chridiss −0,023, busmexpo −0,022, culmsent −0,021, AyrmThes/22 −0,011, cingdei −0,010) |

- Critère (somme plus haute avant toute validation) : **non tenu → W02d REJETÉE** ; CRITERE non mesuré (inutile une fois le premier volet manqué). W02c (pas de W02 sur le romain) reste la règle.
- Lecture : le modèle d'écriture ne corrige pas le défaut observé avec `lat` ; sur l'antiqua ancienne, Tesseract place ses coupures moins bien que le DTW, quel que soit le modèle latin. Le levier restant pour le romain est un aligneur CTC entraîné sur l'imprimé ancien (CATMuS-Print, zenodo.org bloqué).
