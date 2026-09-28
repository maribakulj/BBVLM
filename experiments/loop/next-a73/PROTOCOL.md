# A73 — propositions ligne dans les vides YOLO, diagnostic consommé

Claude est inchangé à `76056c5c1957e0de4232f0aef1f6cbc7f2893402` ; le parent
Codex A72 est `562fba3d0f494bfb105f02f28331d700a9051939` et master reste
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun merge.

## Hypothèse gelée

Le masque A72 a un fort rappel mais n'est pas une boîte. Construire des
propositions uniquement pour les composantes de classe ligne dont au moins 50 %
des pixels sont hors de l'union des rectangles YOLO A69. Connexité 8, aire
minimale quatre pixels, boîte englobante de la composante entière. Les classes
YOLO utilisées sont exactement les candidats A69 scellés, donc figures et
séparateurs restent exclus comme alors. Aucun XML n'intervient dans la
proposition ; le JSON candidat est écrit et haché avant score.

Deux pages A72 déjà consommées seulement. Aucun nouveau forward Eynollah/YOLO,
OCR ou VLM. Cette règle simple évite l'expansion globale et teste si la passe
pixelwise peut devenir un étage de rappel payé seulement quand YOLO laisse des
zones de texte.

## Mesures et gate local

- proportion des 33 lignes A70 sans contributeur récupérées à au moins 50 % par
  l'union des nouvelles propositions ; gate : au moins 80 % ;
- fraction de l'union des boîtes proposées située dans l'union PAGE des lignes ;
  gate : au moins 75 % ;
- nombre de propositions avec moins de 1 % de leur aire dans toute ligne PAGE ;
  gate : zéro ;
- propositions, aires, temps et hashes par page.

Ces seuils sont fixés avant ouverture des XML pour A73. Leur passage ne vaut ni
validation indépendante, ni précision objet, ni boîte ALTO parfaite. En cas de
succès, geler la règle sur des pages diverses non encore inférées ; en cas
d'échec, ne pas régler les seuils sur ces pages.

## Source primaire et code

Liebl & Burghardt, arXiv:2004.07317, texte complet lu le 28 septembre 2026 :
leur étude de segmentation pixelwise de journaux compare 11 backbones et neuf
configurations, constate que le tuilage vertical est généralement robuste, et
signale explicitement le risque de fusion de régions adjacentes. Cela motive la
restriction aux vides YOLO et la mesure de contamination, pas un nouveau modèle.
Le code actuel Eynollah 0.9.2 relu reste celui consigné en A72 ; aucune autre
dépendance n'est installée.
