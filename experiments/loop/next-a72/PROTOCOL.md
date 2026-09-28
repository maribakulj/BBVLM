# A72 — rappel pixelwise minimal Eynollah sur absences YOLO consommées

Claude est inchangé à `76056c5c1957e0de4232f0aef1f6cbc7f2893402` ; le parent
Codex est `d6fa389b6e4a2c26b5e3e1518cd9e565a60e8029` et master reste
`60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun merge.

## Hypothèse gelée

A71 montre du texte visible dans 11/12 absences, mais seulement cinq récupérations
rectangulaires sûres. Tester uniquement le modèle de lignes Eynollah 0.9.2,
sans ses étages page, régions, OCR ou ordre de lecture : une passe pixelwise peut
récupérer au moins la moitié des lignes sans contributeur YOLO sur deux pages
A69 consommées et typographiquement éloignées.

Pages fixées avant inférence : `Reichs_Post_Reuter_1700-11-16_0001` et
`Koelnische_Zeitung_1924_0001`. Les images sont redimensionnées à 2000 px de
large (ratio conservé), puis tuilées 672×672 avec 10 % de recouvrement, comme le
chemin `do_prediction_new_concept` inspecté dans Eynollah. Modèle exact :
`modelens_textline_0_1__2_4_16092024.onnx`, SHA-256
`bc6575898c41bba852b3c5367c92add6663ba121e45c325fe770e1cc05241e5c`.
CPU ONNX, quatre threads ; aucun autre poids Eynollah n'est téléchargé.

## Mesure et gate local

Après scellement des masques image-only, ouvrir les mêmes XML consommés. Une
ligne est touchée si la classe texte brute couvre au moins 1 % de son polygone
rastérisé. Gate local : au moins 50 % des lignes A70 à zéro contributeur sont
touchées, sans conclusion de boîte parfaite. Rapporter aussi toutes les lignes,
temps, tuiles et pixels positifs. Les polygones PAGE restent une référence de
diagnostic imparfaite ; aucun texte, aucune page Test et aucune GT ne sont
modifiés.

## Décision

Si le gate passe, conserver cette passe comme candidat de rappel sélectif et
définir ensuite un routeur image-only avant toute validation diverse. Sinon,
rejeter le coût Eynollah et pivoter vers OLR/retrieval. Ce protocole ne mesure ni
CER, ni ALTO mot, ni article, ni métadonnées.

