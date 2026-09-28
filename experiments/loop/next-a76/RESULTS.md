# A76 — résultat du transfert indépendant

## Résultat principal

La règle A75 ne transfère pas. Sur quatre nouvelles pages Training gelées avant
pixels et annotations, elle produit 1 306 candidats pour 1 103 lignes :

- IoU50 : précision 72,74 %, rappel 86,13 %, F1 78,87 % ;
- IoU70 : précision 64,78 %, rappel 76,70 %, F1 70,24 % ;
- IoU assignée moyenne : 0,6962.

Tous les seuils scientifiques sauf l'absence de pages Test échouent. La règle
n'est donc pas promue et les seuils ne sont pas abaissés.

## Hétérogénéité

| Page | Candidats/références | P/R IoU50 | P/R IoU70 |
|---|---:|---:|---:|
| 1626 | 40/34 | 85,00/100,00 % | 82,50/97,06 % |
| 1785 | 92/91 | 93,48/94,51 % | 88,04/89,01 % |
| 1866 | 708/650 | 78,53/85,54 % | 72,18/78,62 % |
| 1924 | 466/328 | 58,80/83,54 % | 47,42/67,38 % |

L'agrégat A75 masquait donc une forte dépendance au type de page. Les journaux
denses récents génèrent beaucoup plus de composantes que de lignes et une forte
fragmentation/ambiguïté d'appariement ; une composante binaire n'est pas une
instance de ligne robuste.

## Coût et invariants

- 84 vraies tuiles Eynollah CPU ; 109,53 s pour inférence, extraction et score ;
- prédictions et candidats hachés avant ouverture des XML sélectionnés ;
- zéro OCR, zéro VLM, zéro page Test ; originaux et références inchangés ;
- règle A75 inchangée, sans réglage après score.

## Conclusion

Conserver Eynollah comme signal dense de rappel, mais rejeter le rectangle de
chaque composante comme générateur général de boîtes. A77 doit attribuer, sur
ces données désormais consommées, les échecs aux fusions/fragmentations et à la
convention PAGE, puis figer soit une vraie séparation par pics-vallées/centre de
ligne, soit avancer un étage OLR distinct. Aucun gate global n'est validé.
