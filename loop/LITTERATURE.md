# Revue de littérature

Accès : arxiv/HAL bloqués par le proxy — résumés obtenus par recherche web.
Chaque entrée : source, apport, limite, conséquence pour BBVLM.

## L01 — OCR texte par VLM (2026-09-28, avant O01)

- **Greif et al. 2025**, *Multimodal LLMs for OCR, OCR Post-Correction, and NER
  in Historical Documents* (arXiv 2504.00414). Annuaires allemands 1754-1870.
  Gemini 2.0 Flash : CER normalisé 1,27 % en OCR direct, 0,11 % sur de
  l'Antiqua ; **post-correction multimodale (image + OCR existant) < 1 % de
  façon constante**, sans fine-tuning. *Limite* : CER normalisé, corpus
  d'annuaires, pas 0 %. *Conséquence* : la lecture image + texte candidat est
  une piste établie, à ne pas présenter comme nouvelle.
- **Évaluations 2025-2026** (arXiv 2510.06743 ; OCR Arena) : Gemini 2.5 Pro
  3,36 % sur documents historiques ; en tête d'OCR Arena début 2026 : Gemini 3,
  Claude Opus 4.6, GPT-5.2. *Conséquence* : aucun système publié n'annonce 0 %
  sur une page historique complète ; le 0 % reste à démontrer.
- **Clérice et al. 2026**, *Reading or Guessing?* (arXiv 2605.27750). Les VLM
  produisent des erreurs fluentes (substitutions plausibles, répétitions,
  balisage) absentes des OCR classiques ; sous perturbation contrôlée des
  caractères, ils s'éloignent plus du texte affiché. *Conséquence* : un
  contrôle d'ancrage visuel est nécessaire ; l'exactitude moyenne ne prouve
  pas la lecture.
- **OCR-EDR 2026** (arXiv 2609.03445) : diagnostic et réparation par rendu —
  rendre la prédiction, la comparer à la source, boucle édition-rendu-évaluation
  (94,8 % de diagnostic). *Conséquence* : pont possible avec le coût
  d'ajustement texte/encre de master (`correct.py`) : vérifier sans référence.
- **HIPE-OCRepair (ICDAR 2026)** et *No Free Lunches* (2025) : la
  post-correction LLM texte seul dégrade souvent ; l'image est nécessaire.
- **Double saisie** (pratique classique de production de VT) : accord de deux
  lecteurs indépendants = présomption ; déjà mesuré dans master (B37).

## L02 — conventions de la référence (2026-09-28, après O02, avant O03)

- **OCR-D, *Ground Truth Guidelines*** (github.com/OCR-D/gt-guidelines, lu
  dans le dépôt). Niveau 2 : ligatures consonantiques décomposées, e suscrit
  codé voyelle + U+0364 et distingué du tréma, ſ distingué, ß pour ſz,
  ꝛ (U+A75B) pour r rotunda, abréviations non développées ; **« Spaces are only
  reproduced as separators of words. Punctuation marks are always added to the
  preceding word. »** Folio, signature et réclame sont des régions distinctes.
  *Conséquence* : une partie des « fautes » O02 étaient des violations de cette
  règle (espace devant la virgule oblique), corrigées de façon déterministe par
  `outils/ocrd2.py`, et la consigne du lecteur doit citer la règle.
- **ROVER** (Fiscus 1997) et le vote multi-OCR (Lund & Ringger) : combiner des
  lectures par alignement et vote. *Limite constatée en O02* : deux lectures du
  même modèle partagent leurs erreurs ; le désaccord A1/A2 ne signale que
  0 à 72 % des lignes fautives selon la page.

## L03 — zoom et alignement (2026-09-28, avant O04 et G01)

- **Zoom multi-résolution des VLM** : Dragonfly (2024, agrandir au-delà de la
  résolution native), ZoomEye (EMNLP 2025, exploration arborescente), CropVLM
  (CVPRW 2026, politique de recadrage apprise, gains en texte de scène et
  documents), DeepEyes (2026). *Conséquence* : vues de détail agrandies pour
  les signes suscrits (O04) ; le recadrage appris dépasse ce qu'on peut faire
  ici (pas d'entraînement), on teste la version sans apprentissage.
- **Alignement texte-image** : CTC transcription alignment (Bullinger, arXiv
  2508.07904) ; alignement sans apprentissage mot à mot avec gestion des sur/
  sous-segmentations (Moccia, PMC9864051) ; kraken 5 ; PERO `force_align` (utilisé
  par astra). *Conséquence* : l'alignement CTC est l'état de l'art quand un
  reconnaisseur est disponible ; ici PERO n'est pas téléchargeable (lien
  bloqué), d'où `connexe` (sans reconnaisseur) comme moteur principal.
- **Évaluation des boîtes** : IoU, précision/rappel, ZoneMap (appariements,
  divisions, fusions). CRITERE.md reste la mesure gelée du projet.

## L05 — OLR, articles, métadonnées (2026-09-28, avant O08)

- **Mocaër et al. 2026, *Towards Hierarchical Structure Understanding of
  Newspaper Images*** (arXiv 2607.15082 ; résumé complet lu dans le dépôt
  d'astra, arxiv bloqué ici). Représentation section → article (article / ad /
  freead) → blocs (title, subtitle, text, illustration, caption, table,
  author…) avec ordre de lecture ; deux voies : pipeline YOLO + LayoutReader +
  segmentation d'articles, et Tiramisu (transformer hiérarchique de bout en
  bout) ; jeu **Finlam La Liberté** (Teklia, HuggingFace — bloqué ici).
  *Conséquence* : c'est le cadre d'évaluation de la presse ; METS pour la
  structure logique, ALTO pour la physique. À reprendre quand l'accès existe.
- **STRAS / LIAS** : séparation d'articles par similarité textuelle (STRAS) ou
  par géométrie et filets (LIAS). **astra A48-A49** : colonnes par modes
  récurrents du bord gauche, ordre global 0,67 → 0,88 sur Finlam — à reprendre.
- **OCR-D GT Guidelines, structure** : types de régions des livres
  (paragraph, heading, header, page-number, signature-mark, catch-word,
  marginalia, footnote, caption…) et ReadingOrder dans le PAGE XML. Présents
  dans toutes nos pages SBB → **OLR des livres mesurable dès maintenant**.
- **Métadonnées par LLM** : ATR4CH (2025) 0,96-0,99 F1 d'extraction de
  métadonnées sur documents patrimoniaux ; MOLE (EMNLP 2025, articles
  scientifiques). *Limite* : sorties instables, à contraindre (schéma, citation
  exacte du texte source). *Conséquence* : les métadonnées seront extraites de
  la transcription diplomatique, chaque valeur citant ses caractères sources.

## L06 — ů et uͤ en haut-allemand imprimé (2026-09-28, après O08)

- **Ad fontes (Université de Zurich), tutoriel « Die frühneuhochdeutsche
  Diphthongierung » et « Gedrucktes Frühneuhochdeutsch »** : la diphtongue du
  moyen haut-allemand *uo* se monophtongue (muot > Mut) ; les imprimés la
  notent par un o suscrit, réduit typographiquement en anneau (ů).
- **Directives d'édition (Heidelberg, Minnereden ; Hartmann von Aue ;
  Haderbücher)** : le e suscrit, sous toutes ses formes (points, demi-arc,
  trait, crochet), note l'inflexion ; un o suscrit note *uo*.
- *Conséquence* (pont linguistique → paléographie) : la forme graphique
  ambiguë sur u se tranche par l'étymologie du mot : diphtongue *uo* (zů, gůt,
  thůn, můt, brůder, blůt, bůch) → ů ; inflexion (für, über, Sünde, müssen,
  führen, dünn) → uͤ. Les 13 références SBB consommées suivent cette règle sans
  exception. Règle R2, à valider sur pages neuves.

## L07 — ligne inclinée ou courbe : centre local (2026-09-28, après O10)

- **OCRopus `lineest.CenterNormalizer` (Breuel, ocropy)** : centre de ligne
  estimé colonne par colonne comme l'argmax de l'encre lissée par une
  gaussienne large (σ vertical 0,5 h, σ horizontal h), puis lissé ; la ligne
  est ensuite redressée autour de ce centre. Sert à normaliser les lignes
  Fraktur avant LSTM. *Apport* : un centre local robuste aux voisines
  (l'argmax suit la ligne dominante de la boîte). *Limite* : conçu pour une
  ligne déjà découpée ; ne dit rien des boîtes de mots.
- **kraken (lignes de base)** : la représentation ligne de base + polygone
  porte déjà la courbure ; nos filtres de composantes (connexe master) ne
  l'utilisent pas et jugent au centre de la boîte englobante.
- *Conséquence* : sur heptaldai (dérive ≈ 40 px sur une ligne), le filtre
  « centre de composante à < 0,45 h du centre de boîte » garde l'encre des
  lignes voisines. On remplace le centre constant par le centre local
  CenterNormalizer, sans rien changer d'autre (expérience B01).

## L08 — une ligne n'appartient qu'à une région (2026-09-28, pendant O11)

- **OCR-D GT-Guidelines, « Absatz » (lyAbsatz) et schéma PAGE** : les
  régions sont des structures distinctes (paragraphe, titre, marginalia,
  signature, date de lettre…), et une TextLine est enfant d'une seule
  TextRegion. Une même ligne visuelle qui porte la fin d'un paragraphe puis,
  après un grand blanc, une formule de date ou de signature alignée à droite
  est donc transcrite en **deux lignes** dans la référence (extraudeu :
  « mit bekannt gemacht. » | « Signatum Breßlau den 5. Febr. 1753. »).
- *Conséquence* : règle candidate P7 (deux blocs de fonction différente sur
  une même ligne visuelle → deux lignes, chacune avec son rôle). Constatée sur
  O11, donc à valider sur les pages suivantes, pas sur extraudeu.

## L09 — ordre de lecture par découpe XY récursive (2026-09-28, pendant O11)

- **Nagy & Seth (1984) ; Ha, Phillips & Haralick, « Recursive X-Y cut using
  bounding boxes of connected components » (ICDAR 1995)** : l'arbre XY coupe
  récursivement la page aux blancs horizontaux puis verticaux (ou au plus grand
  blanc), sur les boîtes englobantes ; un seuil de blanc évite de couper entre
  deux lignes ordinaires. *Apport* : un titre pleine largeur forme une bande à
  part au lieu de fusionner les colonnes. *Limite* : se trompe quand aucune
  bande blanche ne traverse (mise en page en L) — d'où **Meunier (ICDAR 2005,
  Optimized XY-cut)** et **XY-Cut++ (2025, masques hiérarchiques)**.
- *Conséquence* : notre ordre par recouvrement horizontal (union-find) fond
  toutes les colonnes d'une page-tableau dès qu'une ligne les traverse
  (852691769 : 33 lignes non placées sur 80). On teste l'XY-cut classique sur
  boîtes de lignes, seuils relatifs à la hauteur médiane de ligne (S03).

## L10 — aligner une transcription sur les lignes d'image par ancres OCR (2026-09-28, après O11)

- **Feng & Manmatha (2006), « A hierarchical, HMM-based automatic evaluation
  of OCR accuracy for a digital library of books »** et **Yalniz & Manmatha
  (2011), « A fast alignment scheme for automatic OCR evaluation of books »** :
  une OCR imparfaite suffit à aligner un texte exact sur l'image, en ancrant
  sur les mots rares communs (mots uniques), puis en alignant récursivement
  entre ancres. *Apport* : l'appariement se fait par le contenu, indépendamment
  d'un ordre de lecture supposé. *Limite* : conçu pour des livres entiers ;
  bruit d'OCR élevé sur Fraktur.
- **astra A53** : garde le CTC (PERO) comme signal d'alignement mot/ligne, pas
  comme texte. PERO est bloqué ici ; Tesseract 5 + tessdata_best
  (script/Fraktur, lat, deu, GitHub) est installable.
- *Conséquence* (S05) : Tesseract lit chaque ligne kraken (texte jeté, sert
  d'ancre) ; les lignes du lecteur sont appariées aux lignes kraken par
  similarité de texte (hongrois), l'alignement par largeur ne complétant que
  les lignes sans ancre. Vise les pages où aucun ordre fixe ne reproduit
  l'ordre du lecteur (852691769 : blocs lus colonne par colonne).

## L11 — lignes manquées : profils de projection (2026-09-28, après O12)

- **Likforman-Sulem, Zahour & Taconet (2007), « Text line segmentation of
  historical documents: a survey » (IJDAR)** : les profils de projection
  horizontaux sont la méthode de base des lignes non inclinées ; robustes
  aux grandes tailles de caractères, fragiles aux lignes qui se touchent.
- **kraken blla** : réseau entraîné sur des corps de texte courants ; les
  titres en très gros corps (durrgeda : 430 px, initiales florales) ne sont
  trouvés à aucune échelle (1, 1/2, 1/3, 1/5, 1/8) — mesuré.
- *Conséquence* (S06) : seulement s'il reste des lignes lues non placées,
  chercher par projection horizontale les bandes d'encre que les lignes
  kraken ne couvrent pas ; les proposer comme lignes candidates à l'ancrage
  Tesseract (S05). Complément ciblé, pas un second segmenteur.

## L12 — OCR-D gt-guidelines (GitHub OCR-D/gt-guidelines), apostrophe
- Source : dépôt `OCR-D/gt-guidelines` (ocr-d.de bloqué par le réseau) ; `de/trans/trAnfZeichen.dita`, liste de contrôle des ditamaps.
- Apport : ’ U+2019 n'y figure que comme guillemet simple fermant ; la règle
  « trApostrophe » est restée non rédigée (« [ ] trApostrophe.dita => Kommentar »).
  Aucune prescription publiée : la convention effective est celle des VT SBB
  distribuées, qui codent toute apostrophe en ' U+0027 (29 pages, 0 ’).
- Limite : convention observée sur notre échantillon seulement ; d'autres
  corpus OCR-D peuvent coder ’.

## L13 — Breuel 2002 (Two Geometric Algorithms for Layout Analysis) ; Smith 2009 (Hybrid Page Layout Analysis via Tab-Stop Detection, Tesseract)
- Apport : une gouttière de colonne est un grand rectangle blanc, haut et
  étroit, voisin de composantes de taille texte ; il sert d'obstacle aux
  lignes (Breuel). Smith : les colonnes se déduisent de taquets alignés sur
  plusieurs lignes. Une espace de mot n'est jamais alignée d'une ligne à
  l'autre ; une gouttière l'est.
- Limite : pensé pour la page entière ; ici on ne l'applique qu'à couper les
  lignes kraken qui franchissent une gouttière (notes en deux colonnes,
  manchettes collées).

## L14 — Likforman-Sulem, Zahour, Taconet 2007, « Text Line Segmentation of Historical Documents: a Survey » (IJDAR ; arXiv 0704.1267)
- Apport : composantes « chevauchantes » (hampes et jambages entre deux
  lignes) : chacune est attribuée à une seule ligne, selon la part de son
  encre dans chaque bande et la proximité ; une composante qui traverse la
  ligne de base locale appartient à cette ligne.
- Limite : manuscrits surtout ; les composantes réellement « touchantes »
  (deux lignes soudées) exigent une découpe, non traitée ici.

## L15 — confiance déclarée des VLM : « Overconfidence is Key » (Groot & Valdenegro-Toro, 2024, arXiv 2405.02917) ; « Small VLMs Know When They Are Wrong But Cannot Say So » (2026, arXiv 2607.22034)
- Apport : la confiance verbalisée des LLM/VLM est mal calibrée et surtout
  trop haute ; le signal interne existe mais n'est pas exprimé.
- Conséquence : ne pas fonder le choix des lignes à relire sur l'incertitude
  déclarée par le lecteur (hypothèse écartée sans lecture VLM). Le désaccord
  entre deux lectures reste le seul signal mesuré qui marche (P3).
- Limite : études sur VQA/objets, pas sur la transcription diplomatique.

## L16 — Rezanezhad, Baierer, Gerber, Labusch, Neudecker 2023, « Document Layout Analysis with Deep Learning and Heuristics » (HIP '23 ; eynollah, SBB/qurator)
- Apport : segmentation de mise en page et de lignes pensée pour les imprimés
  historiques de la SBB (même fonds que notre VT) ; heuristiques pour
  manchettes, titres, en-têtes ; lignes par masque dense.
- Limite : TensorFlow, modèles 1,9 Go, lent sur CPU ; pas d'ordre ni de texte ;
  à n'utiliser ici que pour retrouver les lignes que kraken manque.

## L17 — Tables des matières : titres + colonne de renvois (S08c)
- Source : « Reconstructing the Table of Contents a PDF Forgot to Ship » (Towards Data Science) ; pdf_oxide issue #1605 (listes à points de conduite prises pour des tableaux).
- Apport : le renvoi aligné à droite est un signal de mise en page propre aux tables ; les moteurs le coupent tantôt trop (cellules), tantôt pas (ligne unique) ; il se traite au niveau des jetons de ligne (texte + position), indépendamment du moteur.
- Limite : sources grand public, PDF natifs, pas d'évaluation ; rien sur le Fraktur ni sur des renvois sans points de conduite. Confirme seulement le choix S08c : couper par jetons (boîtes de mots Tesseract), pas par blancs d'encre.

## L18 — Texte vertical : détecter l'orientation, tourner, relire
- Sources : Tesseract, « Combined Script and Page Orientation Estimation » (OSD, angles 0/90/180/270) ; issue tesseract #3836 (rotation sans reconnaissance) ; « Seeing Straight: Document Orientation Detection for Efficient OCR » (arXiv 2511.04161) : la plupart des OCR et VLM se dégradent fortement sous rotation.
- Apport : la pratique établie est de décider l'orientation (ici par ligne), de tourner le fragment de 90° et de relancer la reconnaissance ; un moteur non orienté produit du bruit sur une ligne debout.
- Limite : OSD pensé pour la page entière, peu fiable sur une ligne courte ; rien de spécifique aux intitulés verticaux des tableaux imprimés anciens. Pour nous : essayer les deux sens (±90°) et garder la lecture la plus proche du texte lu.

## L19 — Lignes courtes manquées par la détection de lignes de base
- Source : Grüning, Leifert, Strauß, Michael, Labahn, « A Two-Stage Method for Text Line Detection in Historical Documents », IJDAR 2019 (arXiv 1802.03345) ; revue « Recent advances in text line segmentation and baseline detection… » (2025).
- Apport : défauts connus des détecteurs de lignes de base : lignes courtes manquées, lignes trop proches fusionnées, fragments. Le second étage de Grüning regroupe de bas en haut des éléments (superpixels) en lignes : complétion par l'encre, pas par le réseau.
- Limite : pas de recette pour compléter une ligne courte détectée partiellement ; leur regroupement demande la carte de lignes de base de l'ARU-Net, que kraken n'expose pas. Pour nous (S09) : prolonger la boîte kraken courte vers les composantes d'encre de sa bande qui n'appartiennent à aucune autre ligne.

## L20 — Alignement transcription–image pour corriger la segmentation en lignes
- Sources : « Automatic Line Segmentation and Ground-Truth Alignment of Handwritten Documents » (ICFHR 2014) ; « End-to-End Transcript Alignment of 17th Century Manuscripts: The Case of Moccia Code » (J. Imaging 2023) ; « OCR-Free Transcript Alignment » (ICDAR 2013).
- Apport : quand une transcription existe, elle sert à corriger la segmentation : l'alignement texte–image absorbe la sur- et la sous-segmentation (lignes fusionnées ou coupées) ; formalisé en transducteurs pondérés (WFST) sur treillis OCR.
- Limite : manuscrits, transcription au niveau document ; 92 % de lignes correctes seulement ; pas de règle simple pour valider une coupe. Pour nous (S02c) : une coupe géométrique n'est acceptée que si le morceau détaché, relu, retrouve une ligne lue — la lecture VLM tient lieu de transcription.

## L21 — Blancs de mots : seuil d'écart adapté à la hauteur de ligne
- Sources : « An Unsupervised and Robust Line and Word Segmentation Method for Handwritten and Degraded Printed Document » (ACM TALLIP 2021) ; CEDAR, « Word Segmentation of Off-line Handwritten Documents » (SPIE 2008) ; Lipi Gnani (arXiv 1901.00413).
- Apport : en imprimé, les écarts entre mots sont nettement plus grands qu'entre lettres ; seuil adaptatif proportionnel à la hauteur de ligne, profil de projection vertical ou regroupement de composantes.
- Limite : rien sur la transcription diplomatique des blancs (espaces imprimés irréguliers, justification) ; seuils empiriques. Pour nous (piste S10) : le blanc lu par le VLM pourrait être vérifié par l'écart d'encre, mais le gain possible est borné (28 lignes / 1265 diffèrent par les blancs seuls, dont la moitié par convention de la VT).

## L22 — Ligne de texte et région (directives OCR-D)
- Sources : OCR-D, Glossar (« Textzeile : suite de mots à l'intérieur d'une région de texte ») ; Ground Truth Richtlinien (ocr-d.de/de/gt-guidelines/trans/), Structure Ground Truth.
- Apport : la ligne est subordonnée à la région : deux blocs de texte appartenant à deux régions (fin de paragraphe et date/signature alignée à droite, texte et renvoi, deux colonnes) forment deux lignes même s'ils partagent la ligne de base. C'est la convention de la VT SBB (extraudeu, hermhyst, 852691769).
- Limite : la page de glossaire ne donne pas de critère géométrique (taille du blanc) ; la décision « deux régions » reste visuelle. Notre consigne P6 dit « une ligne par ligne imprimée », que les lecteurs appliquent à la ligne de base, pas à la région.

## L23 — Abréviation latine « -que » : MUFI et codage OCR-D
- Sources : MUFI character recommendation 3.0/4.0 (folk.uib.no/hnooh/mufi/specs/MUFI-CodeChart-3-0.pdf ; mufi.info) : U+F50D = ligature q + accent aigu + ꝫ (LATIN SMALL LETTER ET, U+A76B), U+E8BF = q ligaturé à ꝫ final ; OCR-D, Ground Truth Richtlinien, « Alphabete, Abkürzungen und Sonderzeichen » (trFremdsprache ; page bloquée par le proxy, consultée via l'index de recherche) : les abréviations sont transcrites telles quelles au niveau 2, avec MUFI quand Unicode manque.
- Apport : le « -que » imprimé (q + signe en forme de 3 ou de point-virgule, avec ou sans accent sur le q) est un seul signe ; « ; » et « ꝫ » en sont deux codages. La VT SBB emploie les deux (7 « q; » sur 76 VT, sinon ꝫ/PUA) → équivalence de codage légitime dans la vue glyphe (T01a).
- Limite : MUFI décrit les caractères, pas la règle de choix entre « ; » et ꝫ ; l'omission du crochet par le lecteur (« q́ » seul) n'est pas un codage mais une faute de lecture — elle se corrige en amont (p2, T01b), pas dans la mesure.

## L24 — Lignes courtes, titres et lettrines en détection de lignes
- Sources : Grüning et al., « Multiple Document Datasets Pre-training Improves Text Line Detection » (arXiv 2012.14163) et « Baseline Detection in Historical Documents using Convolutional U-Nets » (arXiv 1810.09343) : les post-traitements qui écartent les lignes courtes ou quasi verticales font perdre les titres et en-têtes (rappel en baisse) ; Kiessling et al., « Version 5 of the Kraken ATR Engine » (2025) : blla segmente lignes et régions, sans traitement dédié des initiales. PAGE-XML prévoit un type de région « drop-capital » ; les directives OCR-D (ocr-d.de, bloquées par le proxy) n'ont pu être relues.
- Apport : observation directe de la VT SBB (74 pages) : 8 lignes à lettrine (« ES », « DA », « AUf », « WJe », « NEgotium »…) ont la lettrine **dans la boîte du premier mot et de la première ligne** (hauteur du mot 2 à 6× la médiane). Nos lignes kraken commencent après la lettrine → IoU < 0,5 (euanaua, extraudeu), première boîte de mot fausse.
- Limite : la littérature traite la lettrine comme région à part ; la convention SBB (lettrine dans le mot) est déduite des données, pas d'un texte normatif consulté.

## L25 — Séparateurs de mots par reconnaissance (CTC / LSTM) et étendue par l'encre
- Sources : notre banc d'origine (src/boxers/ctcspan.py, B19 : « le CTC donne les séparateurs, l'encre donne l'étendue », Petit Parisien 99,65 % ≤ 0,5c contre 98,18 % pour le DTW seul) ; alignement CTC en HTR (Bullinger, arXiv, cf. L-alignement plus haut) ; Tesseract 5 (LSTM) : boîtes de mots et de caractères hOCR (`hocr_char_boxes`), documentées dans tesseract-ocr/tessdoc (ImproveQuality, Command-Line-Usage).
- Apport : un reconnaisseur situe bien **où** passe la coupure entre deux mots même quand ses boîtes sont lâches ; W01 avait pris les bords de Tesseract (rejeté : bords lâches, ponctuation), la leçon de B19 est de ne lui prendre que le séparateur. Sur BiedBern l. 1, Tesseract (script/Fraktur) met la coupure « nöthigen | Hände » à 708-734, exactement le blanc de la VT, là où notre DTW coupe dans le mot (686-690).
- Limite : le modèle CTC prévu (CATMuS-Print, kraken) est inaccessible (zenodo.org bloqué) ; Tesseract Fraktur/Latin est moins bon sur les écritures mêlées et ne sert que lorsque ses mots s'alignent sur les mots lus.

## L26 — Découpage en paragraphes (OLR)
- Sources : revues sur la segmentation de lignes et la mise en page des documents historiques (IJDAR 2025, « Recent advances in text line segmentation and baseline detection… » ; arXiv 0704.1267) ; docExtractor (arXiv 2012.08191) : la mise en page découpe les régions au niveau du paragraphe ; brevets d'analyse d'alignement (variance des retraits gauche/droite, première et dernière ligne exclues).
- Apport : indices classiques d'un début de paragraphe : retrait de première ligne, dernière ligne courte, blanc interligne accru.
- Limite : sur culmsent (O25), la VT découpe une liste de sentences en 4 blocs sans retrait ni ligne courte distinctifs ; aucun indice géométrique simple ne reproduit ce découpage — pas d'hypothèse ouverte tant qu'un cas à indice visible n'est pas trouvé.

## L27 — Estimer la qualité d'un OCR sans vérité terrain
- Sources : « Evaluation of HTR models without Ground Truth Material » (arXiv 2201.06170) ; « Profiling of OCR'ed Historical Texts Revisited » (arXiv 1701.05377) ; travaux sur l'accord entre deux moteurs OCR comme prédicteur du taux d'erreur (R² élevé rapporté sur des documents modernes).
- Apport : l'accord caractère à caractère entre deux reconnaisseurs indépendants prédit la qualité d'une page ; nous disposons déjà gratuitement d'un second reconnaisseur (Tesseract, lu pour l'ancrage S05).
- Limite : Tesseract est bien moins bon que le VLM sur nos pages (son désaccord mesure aussi sa propre faiblesse : écriture, mise en page) ; le signal peut refléter la difficulté de la page pour Tesseract plutôt que l'incertitude du VLM.

## L28 — Calamari et GT4HistOCR : un reconnaisseur CTC d'imprimé ancien accessible
- Sources : Wick, Reul, Puppe, « Calamari — A High-Performance Tensorflow-based Deep Learning Package for Optical Character Recognition » (Digital Humanities Quarterly 2020 ; arXiv 1807.02004) ; Springmann et al., « Ground Truth for training OCR engines on historical documents in German Fraktur and Early Modern Latin » (arXiv 1809.05501, corpus GT4HistOCR) ; dépôt Calamari-OCR/calamari_models (modèles gt4histocr, fraktur_historical, antiqua_historical, ensembles de 5 votants).
- Apport : reconnaisseur CTC entraîné sur 1500-1900, Fraktur et antiqua, qui donne la position de chaque caractère reconnu — le signal « séparateur » de B19 (CTC) que le placeur n'a plus faute du modèle kraken (zenodo bloqué) ; modèles hébergés dans git (raw.githubusercontent.com accessible).
- Limite : entraîné sur images binarisées nlbin (OCRopus) ; demande TensorFlow ; ses positions sont celles des sorties CTC (pics), pas l'étendue des glyphes — il faut, comme B19, n'en prendre que la coupure entre mots.

## L29 — Prétraitement des modèles Calamari et mots déduits des positions de glyphes
- Sources : [calamari_models](https://github.com/Calamari-OCR/calamari_models) (README) ; [ocrd_calamari](https://github.com/OCR-D/ocrd_calamari) ; Wick et al., « Calamari », DHQ 14(2), 2020.
- Apport : la plupart des modèles sont entraînés sur la sortie nlbin d'OCRopus (binaire) et marchent mieux sur des données semblables (le README dit que gt4histocr aurait été entraîné sur niveaux de gris, ce que contredit notre test : lecture fautive en gris, parfaite binarisée) ; ocrd_calamari exige une image binarisée et déduit la segmentation en mots du texte et des positions de glyphes.
- Limite : ocrd_calamari prévient que ces positions servent à l'extraction et au surlignage, « probablement pas » au traitement d'image : précision des frontières non chiffrée ; d'où l'appariement par rang, prudent, de W03b.

## L30 — Alignement forcé CTC : PERO, kraken, pics d'émission
- Sources : PERO-OCR (github.com/DCGM/pero-ocr, `force_align`/`align_text`) ; kraken 7.1.1 `kraken/align.py` et `kraken/tasks/align.py` (lus dans l'environnement) ; Zeyer, Schlüter, Ney, « Why does CTC result in peaky behavior? », arXiv 2105.14849 (2021) ; tutoriel torchaudio « forced alignment with Wav2Vec2 ».
- Apport : l'alignement forcé impose la transcription connue et cherche son chemin le plus probable dans les émissions (Viterbi) ; un reconnaisseur médiocre en décodage peut rester bon localisateur. PERO l'utilise en production pour positionner le texte.
- Limite : le CTC émet en pics (une trame par caractère, blank ailleurs) : ce sont des positions d'émission, pas l'étendue des glyphes. Il faut donc des frontières entre mots (milieu entre pics) recalées sur l'encre, pas des boîtes de caractères. Une cible fausse s'aligne quand même (pas de rejet intrinsèque). Le code kraken 7.1.1 applique log_softmax à des probabilités déjà normalisées, ce qui aplatit les émissions.

## L31 — Extraction de métadonnées bibliographiques depuis la page de titre
- Sources : BiblioPage, arXiv 2503.19658 (2025) ; notices METS/MODS de la SBB (content.staatsbibliothek-berlin.de/dc/PPN….mets.xml, joignable depuis le 30/09).
- Apport : BiblioPage annote 16 attributs sur des pages de titre scannées (tchèques, époques variées) ; meilleur VLM (GPT-4o) F1 67, détection + OCR F1 59 : la tâche est loin d'être résolue même par de grands modèles. Les MODS SBB donnent une VT de métadonnées par œuvre (auteur nom/prénom, titre abrégé, lieu, imprimeur, année, VD16/VD17, langue, genre).
- Limite : la VT catalogue est normalisée (forme d'autorité des noms, lieu moderne, année en chiffres, titre tronqué « … »), alors que la page imprime des formes anciennes (Hagenaw, M.D.XXIX, génitif latin) ; l'imprimeur est souvent au colophon, absent de la page de titre. La mesure doit donc comparer champ par champ des formes normalisées, et distinguer « absent de la page » de « faux ».
