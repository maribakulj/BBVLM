# S15a — Orli (L35) comme source de lignes manquées par kraken (30/09) — REJETÉE

Protocole : orli_base (zenodo 10.5281/zenodo.20558179), kraken 7.0.3, torch 2.12 CPU, bf16-mixed, polygonize ; venv séparé (venvo) pour ne pas toucher venvk. Mesure : rappel des lignes VT (IoU boîte ≥ 0,5) et récupération des lignes VT absentes de kraken_crit2 (lignes de la chaîne).

| page | lignes VT | kraken (chaîne) | Orli | lignes Orli produites | ligne manquée par kraken : meilleur IoU Orli | temps |
|---|---|---|---|---|---|---|
| euanaua/143 | 22 | 21 | 15 | 43 | « Am I. Sontag » 0,29 | 132 s |
| DasWeL/71 | 26 | 25 | 19 | 90 | « I ĳ » 0,36 | 139 s |

- Orli sur-segmente (lignes coupées aux blancs des vers et des listes), rappel inférieur à kraken, et ne récupère aucune des deux lignes manquées. Rejetée pour cet usage ; pas étendue aux 4 autres pages.
- Constat utile (euanaua) : la ligne « Am I. Sontag » n'est pas absente mais mal cadrée : titre en grandes capitales ornées (encre de y = 552 à 693) ; kraken la coupe en deux morceaux [80,615,570,686] + [638,646,831,677] qui ne couvrent que le corps des lettres ; leur union aurait IoU ≈ 0,47 avec la VT. Piste S15b : union des morceaux kraken d'une même ligne lue + extension verticale à l'encre connexe.
