# A75 — instances de ligne depuis le masque dense

## Statut des données

Les quatre pages A74 sont maintenant consommées. A75 est un diagnostic de
développement : même s'il passe, la règle devra être transférée sans changement
sur un nouveau gel A76. Les 100 pages `Test` restent fermées.

## Hypothèse figée

L'image réelle du masque A74 montre des bandes de lignes déjà séparées par des
vallées noires. A73 a perdu cette géométrie en ne gardant que les composantes
résiduelles hors YOLO. A75 conserve toutes les composantes 8-connexes du masque
complet ayant au moins quatre pixels, sans seuil de forme ni annotation. Pour
chaque composante, il scelle avant XML : contour simplifié à un pixel de masque,
rectangle englobant dans les coordonnées natives et aire.

L'appariement avec les lignes PAGE est ensuite univoque et maximise la somme des
IoU entre rectangles (algorithme hongrois). Aucune lecture du texte n'intervient.
Les scores polygonaux du papier PERO emploient IoU > 0,7 ; A75 rapporte donc
précision/rappel/F1 à 0,5 et 0,7, IoU moyenne appariée, fusions et fragments.

## Seuils locaux

La représentation est éligible au transfert A76 seulement si :

- rappel et précision ligne à IoU ≥ 0,5 sont chacun ≥ 95 % ;
- rappel et précision ligne à IoU ≥ 0,7 sont chacun ≥ 80 % ;
- aucune page n'a un rappel IoU50 inférieur à 90 % ;
- zéro nouvelle inférence et zéro page `Test`.

Ce diagnostic ne certifie ni boîtes parfaites, ni OCR, ni ordre, ni articles.
Les rectangles PAGE sont un oracle imparfait et le masque Eynollah est consommé.

