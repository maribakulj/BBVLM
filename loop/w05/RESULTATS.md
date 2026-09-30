# W05 — résultats (alignement forcé CTC, kraken CATMuS-Print, 60 pages, chaîne)

| lot | état (W03b) | W05 |
|---|---|---|
| O07-O17 | 24 / 44 | **25 / 44** (730277879 ✗ → ✓) |
| O18 | 3 / 4 | 3 / 4 |
| O23 | 2 / 4 | 2 / 4 |
| O24 | 2 / 4 | 2 / 4 |
| O25 | 1 / 4 | 1 / 4 |
| **total** | **32 / 60** | **33 / 60** |

- Frontières : pire écart médian par page **1,04 → 0,44 c** ; pages dont le pire écart dépasse 1 c : **31 → 5** ; part des frontières ≤ 0,5 c : ≈ 100 % sur la plupart des pages (brieetli 95,8 → 100, buchdas 96,3 → 100, berirev 96,9 → 100). Aucune page ne franchit 3 c ; aucune page ne perd CRITERE.
- Contrepartie : IoU médiane par page 0,943 → 0,929, minimum 0,884 → 0,811 (bords collés à l'encre ; seuil CRITERE 0,8 : marge faible).
- Les pages encore en échec le sont presque toutes par des **lignes en échec** (lignes non placées, nombre de mots lu ≠ VT), plus par les frontières : c'est la prochaine cible (segmentation de lignes, lignes courtes, blancs).
- **Adoptée** (critères tenus : 33/60, aucun lot en recul, aucun franchissement de 3 c). Défaut BBVLM_W05=tout, avant W03b/W02 ; repli automatique sur W03b/W02 si kraken est absent de l'environnement (vers_alto sous venv2) : lancer `final` avec le python de l'environnement kraken pour avoir W05. Vérifié sur BrenBreu/72 (34 lignes, 226 mots, ALTO valide).
- Rappel : W04 (décodage + rapprochement de texte) avait échoué ; ce qui fonctionne est l'alignement forcé du texte VLM sur les émissions (L30), avec le correctif du log sur des probabilités déjà normalisées.
- Géométrie isolée (VT imposée) : non terminée (arrêtée après 2 h, processus sans sortie visible) ; diagnostic préliminaire sur 8 lignes : 51/51 ≤ 0,5 c.
