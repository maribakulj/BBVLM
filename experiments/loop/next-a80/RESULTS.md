# A80 — transfert figé : gain modeste confirmé

La règle A79 inchangée passe son critère local sur quatre nouvelles pages Training,
sélectionnées par nom/hachage avant ouverture : +1 correspondance IoU50, aucune
perte de correspondance, précision et rappel non décroissants sur chaque page.
Ce sont désormais des pages consommées. Leur indépendance vis-à-vis de nos réglages
ne prouve pas leur absence de l'entraînement des modèles tiers.

| Page | Propositions avant→après | Précision IoU50 % | Rappel IoU50 % | Gains/pertes |
|---|---:|---:|---:|---:|
| Reichs_Post_Reuter_1700-11-16_0004 | 62→62 | 74.19→74.19 | 100.00→100.00 | 0/0 |
| Holzmindisches_Wochenblatt_1785-07-30_0006 | 66→63 | 43.94→47.62 | 96.67→100.00 | 1/0 |
| Koelnische_Zeitung_1866-06_1866-09_0539 | 629→615 | 88.87→90.89 | 94.91→94.91 | 0/0 |
| Koelnische_Zeitung_1924_0018 | 648→648 | 98.30→98.30 | 93.95→93.95 | 0/0 |

17 liens, 1 405→1 388 propositions. À IoU70 : 1 210→1 213 correspondances.
La précision faible (47,62 % en 1785) demeure ; ce succès relatif ne valide ni
boîtes parfaites, ni mots, ni OCR, ni supériorité globale sur PERO. L'ancien champ
`status` du scoreur routé contient «consumed» par héritage du script A79 ; le
protocole et les empreintes attestent le gel avant ces nouvelles images.

Coût réellement exécuté : 92 forwards de tuiles Eynollah, quatre YOLO ;
étage dense 113.275 s et étage routé 7.364 s,
dont YOLO 6.772 s (CPU quatre threads, hors chargement des
imports/processus et téléchargement). Aucun coût mis à zéro parce que mis en cache.
Zéro OCR, zéro VLM ; 100 pages Test non ouvertes. Sept gates globaux faux.

Invariants : XML source hachés ; prédictions scellées avant XML ; chaque composante
conservée exactement une fois ; algorithme/paramètres A79 inchangés. Les anciens
comptages «candidate_merges_iou_gt10» ne prouvent pas une fusion (audit A77).

Suite A81 : audit aveugle visuel/OCR des propositions A80, rôle/texte/clipping,
sans corriger les originaux ni transformer les références manquantes en texte vide.
Ce diagnostic ne sera pas une nouvelle validation indépendante.
