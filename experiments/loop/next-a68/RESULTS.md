# A68 — résultat : réparation guidée par l'encre, utile mais non promue

La règle image-only a été exécutée sur les cinq pages Validation déjà consommées
par A66/A67 : 168 boîtes texte, 1 317 polygones de lignes, zéro OCR/VLM et zéro
page Test ouverte. Les candidats ont été écrits et hachés avant l'ouverture des
XML d'évaluation.

| Politique | Couverture moyenne | lignes < 95 % | lignes < 50 % | aire ajoutée | aire ajoutée étrangère | boîtes > 1 % intrusion |
|---|---:|---:|---:|---:|---:|---:|
| native rasterisée | 0,979778 | 114 | 8 | 0 | 0 | 0 |
| padding fixe | 0,993302 | 12 | 8 | 3 663 526 | 97 751 (2,67 %) | 28 |
| encre traversant le bord | 0,986296 | 49 | 8 | 1 538 493 | 63 076 (4,10 %) | 17 |

La règle guidée change 122/168 boîtes et améliore 441 lignes sans régression de
couverture. Elle ajoute 42,0 % de l'aire du padding fixe, mais conserve 64,5 %
de son aire étrangère : son taux de contamination par pixel ajouté est donc
plus élevé. Le padding fixe maximise la couverture et améliore 989 lignes, au
prix d'une expansion systématique et de 28 cas d'intrusion > 1 %.

L'overlay post-score confirme que la règle verte récupère le jambage inférieur
de K482 et le bord supérieur de K951 observés par Sol. Il montre aussi que les
grandes boîtes de corps peuvent toucher des règles et colonnes voisines : une
connexion d'encre n'est pas une propriété éditoriale.

Décision : ne promouvoir ni le padding fixe ni `ink_crossing` sur ces données
consommées. Transférer la règle `ink_crossing` inchangée vers un sous-ensemble
Validation divers et non ouvert, avec candidats image-only scellés avant score.
Les 100 pages Test restent réservées. Aucun des sept critères globaux ne change.

Coût : 19,51 s CPU pour l'expérience, 9 tests unitaires de la primitive passés,
aucune nouvelle dépendance lourde, aucun appel VLM/OCR.
