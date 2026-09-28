# A82 — isolation par contour prédit, sans OCR additionnel

Défaut A81 : un rectangleIoU96,86 % inclut45,19 % d'encre attribuée à d'autres
lignes. Développement sur les six cibles A81 appariées déjà consommées.
Une seule règle fixée : union des contours Eynollah prédits correspondant aux
composantes du groupe A80, rasterisée dans le crop natif ; dilatation elliptique
rayon2pixels natifs ; blanchir l'extérieur. Aucun contour/texte GT en entrée.
Images originales et crops non masqués conservés ; masques et dérivés hachés
avant attribution aux polygones PAGE.

Critère local mécanique : conserver>=99,5 % de l'encre Otsu située dans le polygone
assigné, POUR CHAQUE cible ; réduire>=90 % l'encre attribuée aux voisins du cas
contaminéV243d7aaa, sans augmenter cette contamination ailleurs. Le score n'est
qu'un proxy dépendant des annotations et du seuillage, pas une preuve de glyphes
complets. Zéro global gate. Si la règle échoue, ne pas régler le rayon sur ces scores.
Si elle passe, une nouvelle lecture Luna aveugle des6crops seuls mesure OCR/rôle.
Pas de contexte ajouté ; changement de présentation/session = confondant déclaré.
Ce n'est pas une validation indépendante ni une attribution causale Luna/Sol.
