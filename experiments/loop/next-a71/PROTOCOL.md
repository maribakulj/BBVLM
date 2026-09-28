# A71 — audit visuel aveugle des lignes sans boîte

Claude est inchangé à `76056c5c1957e0de4232f0aef1f6cbc7f2893402` ; Codex
part de `80d1c7ebb4ffa2a10f09b57e363ba8c9282b136c`, master reste
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun merge.

A70 montre que 63 lignes profondes n'ont aucune boîte contributive. Sélectionner
12 lignes, maximum deux par page, par hash déterministe des IDs après exclusion
de toute valeur textuelle. Produire des crops de contexte natifs, IDs opaques et
hashes stricts. Un seul lecteur Luna classe chaque vue : `visible_text`,
`non_text_or_rule`, `ambiguous`, et indique si un rectangle de rappel serait
sûr. Aucune transcription ni référence alternative n'est fournie. Les réponses
servent à choisir un outil, pas à modifier la GT ou valider des boîtes parfaites.

Eynollah a été inspecté au head `15ddb7750e132462321a3d57b2a2b74cb8f2b151`
(v0.9.2, 28 juillet 2026). Le README actuel expose segmentation pixelwise de dix
classes, lignes, régions, séparateurs et OLR, avec traitement potentiellement
lent et dépendances ONNX/CUDA. Le papier primaire Rezanezhad et al. HIP 2023 est
accessible ici au niveau abstract/métadonnées seulement : CNN pixelwise plus
heuristiques de marginalia/ordre, trois jeux historiques ; DOI
10.1145/3604951.3605513. Ne pas installer ce gros outil avant confirmation
visuelle que le défaut est du texte réellement manqué.

Les pages A69 sont consommées ; 100 Test restent fermées. A71 ne produit aucun
CER, OLR ou gate global.
