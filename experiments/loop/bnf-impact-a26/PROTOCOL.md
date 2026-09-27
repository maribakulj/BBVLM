# A26 — validation BnF/IMPACT française, multi-document, CTC/Otsu v1

Ce protocole, l'évaluateur et le split sont figés avant extraction ou lecture
des membres du ZIP. La source officielle BnF décrit le lot comme des pages de
presse en français corrigées manuellement, avec zones et transcription en PAGE
XML. L'archive `impact.zip` a été téléchargée depuis le partage BnF ; avant ce
gel, seule sa table centrale (noms, tailles, CRC) a été lue.

## Split

Une page par groupe de noms : le premier PAGE XML lexicographique de chacun des
quatre préfixes documentaires visibles dans le manifeste ZIP. L'image est liée
uniquement par l'identifiant du nom de fichier. Aucun XML, pixel, tableur ou
document interne n'est lu pour sélectionner ces pages.

## Candidat figé `ctc_raw_otsu_v1`

1. Polygones de ligne et texte PAGE fournis ; baseline horizontale synthétique
   à 80 % du rectangle de ligne.
2. PERO OCR 0.7.0, poids publics
   `pero_eu_cz_print_newspapers_2022-09-26`, CPU quatre threads, ParseNet coupé.
3. Alignement forcé d'un proxy NFC limité au codec sur les logits CTC ; le
   texte évalué/exporté n'est jamais remplacé par le proxy.
4. Séparateurs aux milieux arrondis des boîtes CTC voisines.
5. `IMREAD_GRAYSCALE`, un seul `THRESH_BINARY_INV|THRESH_OTSU` sur le rectangle
   source de chaque ligne, sans marge ni filtrage de composantes. Chaque cellule
   est semi-ouverte ; sa boîte est l'enveloppe de tous les pixels non nuls ;
   cellule vide → repli sur la boîte CTC.

Cette règle est l'implémentation A25, importée sans modification. A26 ne teste
pas une segmentation de lignes end-to-end ni un OCR VLM : il teste la géométrie
de mots conditionnée par ligne, texte et ordre des tokens oracle.

## Mesures et promotion

- CTC/Otsu : appariement par index seulement si les comptes source/texte/ALTO
  concordent ; sinon la ligne est entièrement manquante.
- PERO natif : appariement hongrois maximisant la somme des IoU.
- Micro global et par page : complétude, IoU moyenne, rappel/précision à 0,5 et
  0,8, lignes entièrement ≥0,8, erreurs de bords horizontales/verticales.
- CER PERO natif strict et `glyph_decomposition_v1`, séparés de la géométrie.
- Temps de chargement, reconnaissance et alignement, hashes et versions.

Promotion conditionnelle seulement si, sur **chaque page** : zéro omission,
rappel IoU≥0,5 = 1, rappel IoU≥0,8 ≥ 0,90, IoU moyenne ≥ 0,90, rappel IoU≥0,8
strictement supérieur aux deux comparateurs, et IoU moyenne/rappel IoU≥0,5 non
inférieurs. Même un succès ne ferme pas le gate end-to-end ou « boîtes
parfaites » sans lignes prédites et adjudication indépendante.

## Référence et invariants

Les fichiers BnF restent intacts. « Vérité terrain » signifie ici transcription
manuelle et zones déclarées par le producteur ; ce n'est pas une certification
sans erreur. Le rapport vérifie langue observée, correspondance texte ligne/mots,
comptes, empreintes, absence de modification et chronologie du scellement.
