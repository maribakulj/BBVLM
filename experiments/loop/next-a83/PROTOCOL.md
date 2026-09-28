# A83 — coûts et géométrie des seuls étages PERO layout/crop

Comparer sur les quatre pages A80 consommées la configuration publique PERO
newspapers2022-09-26, en désactivant RUN_OCR et RUN_DECODER et en activant
RUN_LAYOUT_PARSER et RUN_LINE_CROPPER. CPU4threads. Préserver configuration exacte,
versions, hashes, latence chargement/layout/crop ; aucune transcription/logit OCR
ne doit être produit. Les images restent identiques à A80.

Géométrie : appariement hongrois rectangleIoU50/70 identique A80. Pour les six cibles
A81, choisir la ligne PERO de meilleur IoU au rectangle prédit A80 SANS consulter
XML, obtenir crop par baseline/hauteurs et mapping ; sceller avant XML. Mesurer
contamination au moyen du mapping et des polygones PAGE, pas par une comparaison
d'aires à des résolutions différentes. Rapporter les lignes non appariées.
Ce développement consommé ne promeut aucun gate global. Aucun réglage sur scores.
Restaurer les poids publics connus ; package0.7.0, dépendancesCPU, reconnaître
qu'un import de module n'est pas une inférence. Pas de coût du reconnaisseur.
