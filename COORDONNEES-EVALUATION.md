# Coordonnées des références — correction de l'évaluateur

Déclaration du 6 octobre 2026, avant les nouvelles notations converties.
Les seuils, les pages sélectionnées et la convention textuelle de PROTOCOLE.md
restent inchangés. Aucune référence n'entre dans la production.

Les deux ALTO BNL déclarent `MeasurementUnit=mm10`. L'évaluateur précédent
traitait leurs valeurs comme des pixels, ce qui rend ses mesures de détection,
son appariement textuel et sa géométrie invalides pour ces deux pages. Les
rapports précédents sont conservés et identifiés comme diagnostics à unités
incompatibles ; ils ne servent pas à établir un gain de qualité.

La conversion officielle est `pixel = mm10 * DPI / 254`, ou
`pixel = inch1200 * DPI / 1200`.
[Source ALTO, Library of Congress](https://www.loc.gov/standards/alto/description.html).

La BNL documente des originaux TIFF à 300 PPI ainsi que son jeu de blocs bruts
image/ALTO. Les fichiers XML locaux désignent ces TIFF ; les PNG locaux ne
conservent pas la densité dans leurs métadonnées. La notation emploie donc
explicitement la résolution documentée du corpus, `--reference-dpi 300`, et
enregistre la transformation. Cette résolution provient de la documentation,
sans ajustement sur les boîtes ou sur les scores.
[Source BNL, Original Images et Raw Ground Truth Pack](https://data.bnl.lu/data/historical-newspapers/).

Le chargeur refuse désormais les unités physiques sans résolution explicite,
ainsi que les unités absentes/inconnues. La transformation s'applique à tous
les bords des lignes et des mots ; elle ne modifie ni le texte ni les refus.
Les coordonnées PAGE et ALTO `pixel` restent à leur échelle déclarée. Si une
image s'avère redimensionnée par rapport à son original, sa résolution effective
doit être établie indépendamment avant certification.
