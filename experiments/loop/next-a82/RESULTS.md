# A82 — rejet du masque de contour prédit

La règle unique gelée (union de contours prédits + dilatation2px natifs) réduit
fortement l'encre voisine, mais échoue au seuil de conservation99,5 % sur4/6cibles.
Elle est rejetée, sans réglage du rayon ni nouvelle lecture payée.

| ID consommé | Encre assignée conservée % | Encre voisine avant→après | Conservation>=99,5 % |
|---|---:|---:|---|
| V243d7aaa | 99.255 | 19275→28 | non |
| V82cc0195 | 99.941 | 400→0 | oui |
| Vde9f1e1c | 99.182 | 17→0 | non |
| V31521ffb | 99.514 | 217→0 | oui |
| Vf9528632 | 98.844 | 161→2 | non |
| V6011b467 | 99.251 | 388→8 | non |

Sur le cas incliné,99,85 % de l'encre voisine est retirée, mais159pixels attribués
à la ligne disparaissent aussi. Inspection effective des PNG Pfefd7445 et P40928fe3
par l'agent principal : le voisinage est masqué et le contour reste serré ; les
pertes ne sont pas déclarées toutes des glyphes, car Otsu et PAGE sont imparfaits.
Ne pas confondre amélioration visuelle et conservation prouvée des informations.

Coût1.391s CPU, dont1.316s préparation et
rendu ; zéro inférence. Six images dérivées et masques sont conservés avec les
originaux A81. Candidats scellés avant le score par XML.100Test non ouverts,
aucun gate global. Le lecteur conditionnel n'a pas été lancé car le critère échoue.

Suite : comparer des étages explicites de PERO (layout/crop uniquement) à ces
crops avant de payer OCR/CTC. La restauration de poids/dépendances et leur coût
doivent être comptés. A81/A82 restent consommés ; nouveau gel après développement.
