# R01 — recherche plein texte sur les ALTO produits (0 passe VLM)

`outils/recherche.py` : index vue « recherche » (ſ→s, e suscrit→tréma, ꝛ→r,
ligatures décomposées, casse et ponctuation de bord retirées ; césures de fin
de ligne recollées), retour à (page, boîte). La vue diplomatique reste dans
l'ALTO, jamais réécrite. Requêtes = tous les mots de la référence PAGE ; une
occurrence est retrouvée si une boîte rendue a IoU ≥ 0,5 avec la sienne.

| page | occurrences | rappel | précision |
|---|---|---|---|
| albedm 31 | 186 | **100 %** | 98,4 % |
| culmsent 25 | 194 | 93,3 % | 96,3 % |
| euanaua 143 | 92 | 90,2 % | 91,2 % |
| AphoqvSuS 20 | 118 | 89,0 % | 97,2 % |
| DasWeL 71 | 118 | 85,6 % | 98,1 % |
| berirev 49 | 244 | 85,3 % | 90,4 % |
| 730277879 / 190 | 142 | 81,7 % | 84,1 % |
| herrleyc 41 | 186 | 53,2 % | 61,1 % |

Mesure de bout en bout (texte P3 + lignes kraken + boîtes connexe + index) ;
les manques cumulent boîtes (IoU < 0,5), lignes non placées (herrleyc : 5
manchettes) et erreurs de la référence elle-même (« ii » pour ü…). À
décomposer.
