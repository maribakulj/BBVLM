# A72 — résultat Eynollah lignes, pages consommées

Le modèle de lignes seul d'Eynollah 0.9.2, exécuté par son SavedModel natif,
touche **642/642** polygones de lignes à au moins 1 % et surtout **33/33** des
lignes qu'A70 classait sans aucun contributeur YOLO. Sur ces 33 résidus, la
couverture minimale vaut 69,62 % ; les 33 dépassent 50 % et 29 dépassent 80 %.
Le gate local de rappel (au moins 50 % des absences) passe donc largement.

Coût réel : 48 tuiles 672×672, 65,04 s CPU à quatre threads pour deux pages,
zéro OCR et zéro VLM. Seul le modèle de lignes a été chargé ; aucun étage page,
région, lecture, transcription ou export d'Eynollah n'a tourné.

L'audit oracle postérieur mesure aussi le débordement du masque. Sur la page
1700, 83,97 % des pixels prédits appartiennent à l'union PAGE des lignes et
16,03 % sont à l'extérieur ; sur la page 1924, ces valeurs sont 97,00 % et
3,00 %. Le masque couvre respectivement 88,57 % et 84,68 % de l'union de
référence. C'est un excellent signal dense de rappel, pas une boîte ALTO : il
faut encore convertir ses composantes/bandes en propositions, les associer à
YOLO et mesurer précision, ordre et coût sur une validation diverse gelée.

Les deux pages et les résidus sont consommés. Le seuil 1 %, le modèle, la taille
et la largeur étaient gelés avant le résultat. La contamination n'était pas un
gate préenregistré et reste explicitement post-hoc. Les 100 pages Test sont
intactes, aucune référence n'a été modifiée et les sept critères globaux restent
faux.

L'ONNX Runtime n'a produit aucun masque : deux lancements ont été arrêtés après
une tentative réseau de télémétrie non nécessaire. Le remplacement par le
SavedModel natif a été consigné avant le score, avec mêmes poids/version logique
et six fichiers hachés. Les échecs restent dans l'état de file ; ils ne sont pas
comptés comme expérience scientifique.
