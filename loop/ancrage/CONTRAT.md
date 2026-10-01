# A0 — Contrat d'expérience (ancrage), version 1, gelé le 01/10 avant toute extraction de caractéristiques

## Données et référence
- Source : OCR-D-GT-VD-SBB, révision 481f7235acfc1f78e88b3c2f22f551595c3f2032 (67 œuvres, 348 pages PAGE niveau 2, mots avec Coords). Image : OCR-D-IMG (tif) de la même révision.
- Texte diplomatique d'une ligne = TextLine/TextEquiv/Unicode tel quel (NFC). Mots = éléments Word de la ligne, dans l'ordre du document. Vérifié en A1 : la jonction des Word par une espace redonne la ligne ; sinon la ligne est exclue et comptée.
- Boîte de référence d'un mot = enveloppe xyxy semi-ouverte des points Word/Coords, en pixels de la page originale (convention « enveloppe d'encre VT », ponctuation selon le découpage VT).

## Occurrence
- Clé = (page, ligne, version_texte = sha256 du texte du bloc, début, fin) — début/fin = offsets en caractères dans le texte du bloc (lignes jointes par « \n »). Jamais la seule chaîne de surface ; deux « und » d'un bloc sont deux occurrences.
- Statuts de sortie : matched / partially_compatible / unresolved ; géométrie nullable dans les propositions uniquement.

## Blocs
- Bloc = 3 à 8 lignes consécutives d'une même TextRegion (paragraphe, note, manchette), tirage déterministe sha256(page+région) ; crop = union des boîtes de lignes + marge 16 px (les lignes voisines hors bloc peuvent apparaître : cas réel).
- Transformation enregistrée : origine du crop (x0, y0), facteur d'échelle s du processor (smart_resize Qwen3-VL), dimensions avant/après ; test aller-retour page→crop→entrée modèle→crop→page exact avant arrondi.

## Partition (par œuvre, jamais par page)
- h = int(sha256(œuvre), 16) mod 20 : h < 4 → **test** (≈ 20 %), 4 ≤ h < 7 → **dev**, sinon **train**. Toutes les pages d'une œuvre vont dans la même partition.
- Biais déclaré : G0 (W05+W06) a été réglé sur des pages de 66 de ces œuvres (boucle O07-O28) ; les pages de test lues par la boucle sont signalées et rapportées à part.

## Bras de E1 (transcription correcte imposée)
- G0 : géométrie actuelle BBVLM (W05+W06 sur boîte de ligne VT et texte VT) — comparateur hors candidat.
- G1a : cartes d'attention de têtes de localisation (L55), sans entraînement (têtes choisies sur train).
- G1 : sonde sur états du décodeur seuls (requête = état après consommation des sous-tokens du mot) → rectangle.
- G2 : G1 + attention croisée dense sur la carte visuelle fine avant fusion (dim 256, positions 2D).

## Mesures et décision (gelées)
- CRITERE par œuvre de test (≤ 0,5 c ≥ 95 %, pire ≤ 3 c, iou_med ≥ 0,8, 0 ligne en échec) + IoU médiane, p95/p99 des erreurs de frontière (en caractères), taux d'échec ; coût (s/bloc CPU).
- H1 (accessibilité) tenue si G1 ou G2 passe iou_med ≥ 0,8 sur ≥ 50 % des œuvres de test.
- H2 (détail visuel) tenue si G2 − G1 ≥ +0,02 d'IoU médiane ET ≥ +2 points de ≤ 0,5 c, IC 95 % bootstrap par œuvre excluant 0.
- Go vers E2/E3 : H1 tenue et G2 non inférieur à G0 (nombre d'œuvres au CRITERE ≥ G0, pire cas ≤ G0 + 0,5 c) — sinon rapport « localisateur conditionnel non compétitif à l'échelle CPU ».
- Échelle CPU (écart au plan) : ≈ 1 500 blocs train, 300 dev, ≥ 400 test (≥ 1 000 lignes test visé), backbone gelé, une graine de développement (17), candidat final graines 17/43.
