# A75 — résultats

Sur les quatre pages A74 désormais consommées, les composantes 8-connexes du
masque complet donnent 1 402 instances pour 1 406 lignes de référence.

- IoU50 : précision 97,36 %, rappel 97,08 %, F1 97,22 %.
- IoU70 : précision 94,58 %, rappel 94,31 %, F1 94,44 %.
- IoU moyen des 1 385 paires assignées : 0,8097.
- Toutes les conditions préenregistrées passent ; aucune inférence, OCR, VLM ou
  page `Test` supplémentaire.

Le résultat agrégé cache une hétérogénéité utile : la page de 1617 a un rappel
IoU50 de 94,12 % mais seulement 74,42 % de précision à cause de neuf propositions
excédentaires (43 pour 34 lignes). Les trois pages plus tardives atteignent
92,31–99,07 % de précision et 96,62–100 % de rappel IoU50.

La représentation est donc éligible à un transfert A76 sans changement, mais
pas promue. A76 doit geler de nouvelles pages, ajouter avant score un seuil
minimum de précision par page au protocole (sans modifier la règle d'instances)
et rapporter séparément les titres/petites composantes. Les comptes
fusion/fragment à IoU>0,1 sont seulement des indicateurs grossiers car des
rectangles de lignes adjacentes peuvent se chevaucher verticalement.

