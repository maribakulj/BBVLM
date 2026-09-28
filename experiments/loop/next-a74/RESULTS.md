# A74 — résultats

Le transfert figé du masque dense Eynollah réussit ses trois seuils locaux sur
quatre pages `Training` nouvelles couvrant 1617, 1813, 1866 et 1924.

- 1 406/1 406 lignes ont au moins 1 % de couverture (100 %, seuil 99 %).
- 98,32 % des pixels positifs du masque sont dans l'union des polygones ligne.
- 84,09 % de l'union des lignes est couverte par le masque (seuil 50 %).
- La précision surfacique par page va de 97,40 % à 99,57 %, donc les quatre
  pages dépassent le seuil de 75 %.
- 84 tuiles Eynollah ont été réellement inférées en 93,19 s CPU ; aucun OCR,
  aucun VLM, aucun DocLayout-YOLO et aucune page `Test`.

Le premier score post-inférence a été interrompu par une allocation d'un masque
pleine page pour chaque ligne. Les quatre prédictions avaient déjà été écrites
et hachées. Le scoreur corrigé rasterise chaque ligne dans sa boîte locale et
réutilise les masques : zéro nouvelle inférence au retry, mêmes pixels scellés.

Ce résultat est important mais limité : il valide le masque comme étage peu
coûteux de preuve de ligne sur ce gel divers, pas comme boîtes ALTO. A73 a déjà
montré qu'une boîte englobante naïve détruit cette précision. A75 doit donc
séparer les lignes/centres à partir du masque selon une méthode figée inspirée
du code Eynollah actuel, puis mesurer appariement et contamination ; aucune
promotion globale avant un nouveau gel indépendant et une adjudication.

