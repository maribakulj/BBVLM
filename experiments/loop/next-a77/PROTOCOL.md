# A77 — attribution des échecs A76 (consommé)

Gel avant calcul : 28 septembre 2026. Aucun nouveau candidat, seuil de promotion,
texte ou référence ne sera modifié. A76 demeure un échec indépendant consommé.

Reprendre les quatre masques scellés et les composantes A75 inchangées. Rasteriser
les vrais polygones PAGE à la résolution du masque et compter leur intersection
avec chaque label connexe. Une arête substantielle exige au moins 20 % des pixels
de la composante ET 1 % de la surface raster de la ligne. Rapporter aussi les
composantes contenues à >=80 % dans une ligne, les références touchées par
plusieurs composantes représentant chacune >=5 % de leur surface, et la part des
pixels prédits qui appartient à plusieurs polygones de référence. Ces seuils
servent à décrire, jamais à certifier une fusion/fragmentation visuelle.

Comparer aux anciens compteurs de rectangles IoU>0.1, qui peuvent confondre
chevauchement d'enveloppes et fusion. Calculer un plafond oracle explicite :
regrouper les composantes dont >=80 % des pixels appartiennent à une même ligne
(choix de la ligne par intersection maximale), puis mesurer les rectangles unions.
Il utilise la référence : diagnostic seulement, jamais déployable ou indépendant.

Produire six exemples déterministes des lignes fragmentées/ambiguës de la pire
page, avec image originale et superposition séparées pour inspection visuelle.
Ne pas ouvrir les 100 Test. Zéro réseau neuronal/OCR/VLM dans le calcul CPU.
Vérifier hashes d'entrée avant/après, comptes et bornes ; conserver chaque échec.
