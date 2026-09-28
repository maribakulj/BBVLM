# A76 — transfert indépendant des instances de lignes Eynollah

## Question

La règle d'instances A75, figée sur des pages désormais consommées, conserve-t-elle
une précision et un rappel utiles sur quatre nouvelles pages diverses ? Cette étape
évalue des rectangles de lignes PAGE ; elle ne certifie ni des boîtes de mots ALTO,
ni l'OCR, ni l'ordre de lecture.

## Gel avant ouverture

- Source : split officiel `Training` de Chronicling Germany. Aucun fichier `Test`.
- Exclusions : toutes les pages A69 et A74.
- Une page dans chacune des strates 1600–1749, 1750–1849, 1850–1900 et
  1901–1945, choisie par le plus petit SHA-256 de `A76-v1:<identifiant>`.
- Écrire et hacher le split avant téléchargement ; écrire et hacher tous les
  masques, prédictions et candidats image-only avant d'ouvrir les XML sélectionnés.

## Méthode figée

Exécuter exactement l'étage SavedModel Eynollah A72/A74 (largeur 2000, tuiles
672, marge 67). Transformer chaque composante 8-connexe du masque complet d'au
moins quatre pixels en son rectangle englobant natif ; epsilon de contour égal à
un pixel du masque. Aucun seuil ni morphologie n'est ajusté.

Apparier une-à-une les boîtes candidates et les rectangles des polygones PAGE par
algorithme hongrois maximisant l'IoU. Rapporter IoU50 et IoU70, agrégés et par
page, ainsi que fusions et fragmentations indicatives.

## Seuils préenregistrés

Le transfert local réussit seulement si :

1. précision et rappel agrégés IoU50 >= 95 % ;
2. précision et rappel agrégés IoU70 >= 80 % ;
3. **chaque page** atteint précision IoU50 >= 85 % et rappel IoU50 >= 90 % ;
4. aucun fichier `Test` n'est ouvert.

Même en cas de réussite, aucun gate global n'est promu : les annotations PAGE ne
sont pas une vérité parfaite, et il reste à évaluer boîtes de mots, OCR, OLR,
articles, métadonnées et retrieval sur des références indépendantes.
