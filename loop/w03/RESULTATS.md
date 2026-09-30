# W03 — résultats (CTC Calamari GT4HistOCR, coupure vers le blanc d'encre contenant une espace Calamari)

Mesure arrêtée avant la fin (O07-O17 non terminé) : l'échec est net sur les lots neufs.

| lot | état actuel (W02c) | W03 « romain » | W03 « tout » |
|---|---|---|---|
| O18 (Fraktur) | 3 / 4 | 3 / 4 (W02 inchangé) | **0 / 4** |
| O23 | 2 / 4 | 2 / 4 | (interrompu) |
| O24 (Fraktur) | 2 / 4 | 2 / 4 | **1 / 4** |
| O25 (romain) | 1 / 4 | **0 / 4** | 0 / 4 |

- Pire erreur de frontière : 5 à 13 caractères avec W03 (BrenBreu 0,32 → 12,8c ; AphoqvSuS 1,1 → 9,45c ; brieetli 1,32 → 9,58c), contre < 1,5c auparavant. Les taux ≤ 0,5c baissent partout (BrenBreu 100 → 97,4 %).
- Cause : Calamari (modèles entraînés sur images binarisées nlbin, texte lu imparfait : « der ahe aß ihr die nohigen Hande ») place des espaces à l'intérieur des mots ; la règle « un seul blanc candidat contenant une espace » déplace alors la coupure vers un blanc interne éloigné. Les positions votées sont justes quand l'espace est bien reconnue (« der | Nähe »), fausses sinon.
- **W03 REJETÉE**. Piste éventuelle (non testée) : n'utiliser les espaces Calamari que si leur nombre égale celui des frontières lues (appariement par rang), et sur image binarisée comme à l'entraînement.
