# A54 — une passe image+PERO passe le garde de non-régression sur un nouveau lot

A54 fige 16 blocs BnL jamais ouverts en A45, puis exécute PERO 0.7.0 + le
routeur A37 et une seule passe Luna qui voit l'image et le candidat PERO. Les
références XML ne sont ouvertes qu'après scellement des deux sorties. Les 16
images ont réellement été inspectées avec des identifiants opaques.

## Texte

| sortie, 16 blocs | CER strict | CER `search_v1` | CER lexical | exact lexical |
|---|---:|---:|---:|---:|
| PERO | 1,589 % (192) | 0,933 % (112) | 0,529 % (51) | 4/16 |
| Luna brut | **1,250 % (151)** | **0,566 % (68)** | **0,228 % (22)** | **10/16** |
| Luna + garde pré-déclaré | 1,316 % (159) | 0,683 % (82) | 0,311 % (30) | 9/16 |

Sur les sept blocs classés français, le garde passe de 1,308 % à 0,685 % en
`search_v1`, et de 0,870 % à 0,396 % en lexical. Le garde accepte 14 réponses
et rejette deux réécritures dont le journal d'éditions ne reconstruit pas le
texte. Luna n'a signalé aucune incertitude : son auto-évaluation ne route donc
rien.

Les deux portes figées passent : baisse agrégée et zéro régression parmi les
deux blocs PERO déjà exacts en `search_v1`, ainsi que parmi les quatre blocs
déjà exacts en lexical. Sur tous les blocs, le garde améliore 7, égale 7 et
dégrade 2 blocs en `search_v1`; les deux régressions partent de candidats déjà
fautifs. Ce résultat valide localement l'architecture « OCR CPU indépendant +
une correction VLM localisée + refus mécanique des réécritures non
traçables ». Il ne valide pas 0 % : 82 éditions de recherche et 30 lexicales
restent, avec seulement 4/16 blocs exacts en recherche et 9/16 en lexical.

## Géométrie inchangée

Sur les 307 lignes et 1 962 mots de référence, PERO+A37 obtient 98,70 % de
rappel ligne à IoU≥0,5. Au mot, A37 améliore la moyenne IoU de 0,580 à 0,667 et
le rappel IoU≥0,5 de 75,03 % à 80,68 %, mais le rappel IoU≥0,8 n'est que
33,54 %. Sur les sept blocs français, IoU≥0,8 mot n'atteint que 15,81 %.
L'étage de boîtes reste donc explicitement non promu.

## Coût et décision

- 309 lignes reconnues par PERO en 31,12 s CPU, plus 0,50 s de raffinement ;
- une passe Luna groupée sur 16 images ;
- aucun modèle de layout supplémentaire et aucun accès à la référence pendant
  l'inférence.

Conserver ce schéma pour le texte, en durcissant le routeur sur les candidats
non exacts. Ne pas payer le VLM pour les colonnes ou coordonnées physiques. La
prochaine validation complète doit porter sur des pages de presse avec
colonnes, articles, OLR, métadonnées et requêtes de retrieval indépendantes.
La référence BnL originale reste inchangée ; sa déclaration ≥99,95 % n'est pas
une preuve de perfection.
