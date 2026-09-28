# Registre des hypothèses et sources — boucle autonome

Chaque candidat doit référencer une source ou un défaut mesuré. Les articles
motivent une hypothèse ; ils ne constituent pas une preuve du gain sur nos pages.

## G01 — affiner la géométrie après l'alignement natif

- Kodym & Hradiš, ICDAR 2021, *Page Layout Analysis System for Unconstrained
  Historic Documents*, https://arxiv.org/abs/2102.11838.
- Code natif PERO : https://github.com/DCGM/pero-ocr ; version exécutée 0.7.0.
- Clausner, Pletschacher & Antonacopoulos, DATeCH 2014, *Document Representation
  Refinement for Precise Region Description*, DOI 10.1145/2595188.2595198.
  Texte intégral consulté :
  https://primaresearch.org/www/assets/papers/DATeCH2014_Clausner_RepresentationRefinement.pdf

Le troisième travail affine des régions à partir d'objets enfants ; ce n'est pas
une preuve spécifique d'amélioration des boîtes de mots PERO. Hypothèse testée :
après localisation temporelle CTC et vraie projection de crop, un affinage borné
sur les composantes d'encre peut retirer du fond sans couper les glyphes. Risques :
diacritiques, bruit, lettres voisines et incompatibilité avec la convention de VT.

Contrainte : frontières partagées entre mots voisins, respect du polygone de ligne,
conservation des accents/composantes plausibles. Réglages sur développement seul.
Évaluer aussi les dégradations, les échecs et les erreurs extrêmes.

## L01 — choix du détecteur de régions

- Zhao et al., DocLayout-YOLO, 2024 : https://arxiv.org/abs/2410.12628.
  Article consulté ; code https://github.com/opendatalab/DocLayout-YOLO.
  Détection rapide de régions, pas alignement mot ni reconstruction d'articles.
  Les scores sur DocLayNet/D4LA/DocStructBench ne prouvent pas les résultats BnF.
- Eynollah, DOI 10.1145/3604951.3605513 ; documentation actuelle consultée :
  https://github.com/qurator-spk/eynollah. Segmentation patrimoniale, lignes et
  ordre de lecture ; documentation signale un compromis vitesse/qualité et
  Python 3.8–3.11. Ne pas installer aveuglément le paquet complet GPU dans notre
  environnement Python 3.12 ; étudier les modèles ONNX si PERO montre un défaut.

Le choix d'un outil supplémentaire est conditionné à un défaut constaté. Ajouter
plusieurs détecteurs avant cette mesure augmenterait le coût sans gain établi.

## T01 — coût et risques des reprises VLM

Les sorties du pilote ONB montrent des erreurs communes non détectées par le
désaccord et des erreurs persistantes malgré `uncertain=false`. Le routage combine
donc contrôles structurels, alphabet/conventions, incohérences et signaux visuels.
Les propriétés de CHURRO, Dolphin, MinerU2.5, Ar-Q-Former et Finlam ont été examinées
dans l'audit initial ; leurs jeux d'évaluation ne remplacent pas notre référence.

## R01 — recherche avec preuves, indépendante du CER

Sources primaires consultées pendant l'itération :
- Sun et al., *When Good OCR Is Not Enough*, arXiv:2605.00911v1,
  https://arxiv.org/html/2605.00911v1 (InduOCRBench, industriel ; portée différente
  des journaux français). Motive une évaluation des citations et du retrieval
  distincte du CER, pas une extrapolation de leurs scores à BBVLM.
- Ehrmann et al., HIPE-OCRepair 2026, arXiv:2607.08143v1,
  https://arxiv.org/html/2607.08143v1. Post-correction textuelle sans images,
  conventions orientées recherche, surcorrection des entrées peu bruitées.
  Conserver ici une couche diplomatique et une projection de recherche séparées.
- Institutional Newspapers Pipeline, documentation et code primaire :
  https://github.com/institutional/institutional-newspapers-pipeline.
  Pipeline de crops, OCR VLM, typage, NER, thèmes, ordre et embeddings. Sa
  documentation décrit 15 étapes ; ce n'est ni une référence METS/ALTO ni une
  preuve de boîtes de mots parfaites. Le texte intégral du rapport associé
  arXiv:2608.18972 n'a pas été récupéré (accès désactivé) : ne pas prétendre l'avoir lu.
- Documentation SQLite FTS5 : https://sqlite.org/fts5.html.
- Documentation normative METS : https://www.loc.gov/standards/mets/docs/mets.v1-9.html
  et XSD 1.12.1 conservé dans le dépôt ; une validation du conteneur METS ne valide
  pas automatiquement la sémantique des champs embarqués.

Implémentation R01 : index lexical par ligne, texte diplomatique inchangé,
normalisation NFC/ſ et casse pour recherche, accents conservés, IDs et coordonnées
retournés avec chaque résultat. Aucun passage VLM supplémentaire. Les résumés et
interprétations ne sont pas mélangés silencieusement aux citations textuelles.
Cette première baseline n'est pas du retrieval sémantique ou interlingue.

## A01 — qualité de référence et métriques décomposables

- OCR-D Ground Truth Guidelines, consultées le 27/09/2026 :
  https://ocr-d.de/en/gt-guidelines/trans/trLevels.html et
  https://ocr-d.de/en/gt-guidelines/trans/transkription.html. Les niveaux décrivent
  la fidélité et l'usage, mais ne sont explicitement pas un sceau de qualité ;
  OCR-D recommande le niveau 2, la préservation de la langue historique et la
  non-correction des erreurs imprimées. Cela motive des profils explicites plutôt
  qu'une normalisation unique.
- Bourne, Simbeye & Nockels, *The Character Error Vector*, arXiv:2604.06160v1,
  texte intégral consulté : https://arxiv.org/html/2604.06160v1. Le papier sépare
  erreurs OCR, parsing et interaction via SpACER/CDD et évalue 49 pages du journal
  *The Spiritualist*. Il montre aussi qu'un CER séquentiel devient inadéquat sous
  parsing cassé. `bbvlm.metrics.spacer` implémente l'équation publiée ;
  `evaluate_cev.py` utilise les centres de mots faute de boîtes caractère réelles,
  limite explicitement reportée.
- Dataset primaire enrichi associé :
  https://huggingface.co/datasets/Jonnob/the-spiritualist-enriched. Le dataset
  annonce ALTO au mot corrigé manuellement et enrichissement SSU/ordre ; les
  boîtes caractère sont inférées et ne doivent pas servir de vérité géométrique.
- OCR-D-GT-VD-SBB : https://huggingface.co/datasets/SBB/OCR-D-GT-VD-SBB.
  La fiche documente 348 pages, niveau 3, contrôle institutionnel, réparation
  d'incohérences, inspection manuelle et exactitude de capture annoncée 99,95 %.
  Son viewer échoue actuellement sur un conflit de colonnes CSV ; l'archive reste
  distribuée et vérifiée par SHA-256. Domaine surtout livres germanophones/latins.

Résultat de l'hypothèse A01 : NewsEye v1 échoue comme arbitre textuel suffisant.
Sur l'échantillon aléatoire aveugle de 45 lignes, le signal Luna/PERO contre le
distribué atteint 24/45. L'intégrité XML révèle 60 lignes à mojibake récupérable.
L'accord des deux systèmes reste un signal de triage, pas une nouvelle vérité.

Diagnostic CEV sur les trois pages NewsEye : SpACER parsing-only approximatif
0,0052 / 0,0016 / 0,0017 contre OCR-only 0,0272 / 0,0167 / 0,0384. Sous cette
approximation et cette référence bruitée, l'erreur d'extraction vient surtout de
la reconnaissance, pas de la couverture des lignes. Cela ne remplace pas les
métriques d'ordre, de régions ou de mots.

## A02 — SSU/COTe et audit du corpus alternatif

- Bourne, Simbeye & Govia, *The COTe score: A decomposable framework for
  evaluating Document Layout Analysis models*, arXiv:2603.12718v2, texte
  intégral consulté le 27/09/2026 : https://arxiv.org/html/2603.12718v2.
  Les SSU rendent l'évaluation moins dépendante de la granularité des boîtes ;
  COTe sépare Coverage, Overlap, Trespass et Excess. Cela motive de garder les
  unités sémantiques distinctes des objets ALTO physiques et des articles.
- Implémentation primaire actuelle consultée :
  https://github.com/THE-3TC/cotescore, version PyPI 0.2.0 du 12/04/2026.
  L'API accepte une carte SSU et des masques de prédiction. Elle sera pertinente
  après obtention de prédictions de régions comparables ; l'installer maintenant
  ne réparerait pas une référence au mot invalide.
- Fiche NLS du corpus compagnon consultée : 50 pages, transcription Transkribus
  corrigée manuellement, modèle annoncé à 0,86 % CER sur son domaine :
  https://huggingface.co/datasets/NationalLibraryOfScotland/Spiritualist_Newspaper.
  Cette assertion porte sur le texte, pas sur les boîtes `String` enrichies.

Audit local sur la révision exacte du corpus enrichi : les boîtes au mot sont
massivement chevauchantes et 0/49 ALTO valide au XSD standard à cause d'attributs
custom. Le corpus reste candidat pour texte/SSU/ordre après audit indépendant,
mais il est exclu comme arbitre de géométrie au mot. Un split 4/8/37, graine
2026092702, a été figé avant inspection. Sur la seule page développement 0009,
le pilote Luna sans fuite d'ID récupère parfaitement l'ordre connu après une
réparation diagnostique d'un ID, mais fusionne les SSU et confond plusieurs rôles.
La réponse brute ne passe pas le contrat structurel ; aucun résultat n'est promu
en validation.

## A03 — transport des identifiants et ordre comme relations

- Clausner, Pletschacher & Antonacopoulos, *The Significance of Reading Order
  in Document Recognition and its Evaluation*, ICDAR 2013,
  DOI 10.1109/ICDAR.2013.141, texte intégral consulté le 27/09/2026 :
  https://primaresearch.org/www/assets/papers/ICDAR2013_Clausner_ReadingOrder.pdf.
  Le papier représente l'ordre complexe par groupes ordonnés/non ordonnés et
  compare les relations entre paires de régions ; il avertit aussi qu'une sortie
  vide peut être préférable à un ordre faux sur les mises en page complexes.
- Zhang et al., *Modeling Layout Reading Order as Ordering Relations for
  Visually-rich Document Understanding*, arXiv:2409.19672, texte consulté le
  27/09/2026 : https://arxiv.org/abs/2409.19672. Le papier montre les limites
  d'une simple permutation et motive une représentation relationnelle. Son
  benchmark n'est pas de la presse patrimoniale et ne valide pas BBVLM.
- OCR-D, *Structure Ground Truth*, documentation primaire consultée le
  27/09/2026 : https://ocr-d.de/en/gt-guidelines/trans/structur_gt.html. Les
  régions PAGE y sont des annotations de structure à niveaux de granularité
  explicites ; cela renforce la nécessité d'un profil de convention, absent des
  seules étiquettes `SSU_ID` distribuées.

Défaut mesuré visé : sur la page développement A02, Luna avait recopié un ID
haché avec un caractère manquant, invalidant une réponse dont l'ordre était
sinon informatif. A03 remplace cette recopie par des jetons visuels courts,
assignés aléatoirement et strictement reliés aux IDs stables par le programme
après validation. La table de liaison et les références sont cachées au lecteur.

Une passe Luna a réellement inspecté original + overlay pour deux pages de
validation gelées (0003, 0008 ; 42 régions). Résultat positif : couverture brute
exacte des jetons sur les deux pages, sans réparation. Résultat négatif : seuils
de contenu manqués sur les deux pages ; micro ordre 0,8628, rôle 0,7143,
groupement SSU F1 0,4923. L'analyse postérieure montre notamment que le modèle
fusionne des annonces distinctes et traite certains fragments de manchette comme
`OTHER`. Le transport est donc résolu, pas l'OLR/SSU. Aucun appel Sol : l'échec
est structurellement net et un second avis sur les mêmes pages consommées ne
constituerait pas une validation indépendante.

## A04 — ordre colonnaire déterministe avant sémantique VLM

- Hakim et al., *Reading Order Inference for Complex Document Layouts*,
  arXiv:2607.01018v1, texte intégral consulté le 27/09/2026 :
  https://arxiv.org/html/2607.01018v1. Les auteurs distinguent les pages simples,
  où un parcours géométrique suffit, des flux entrelacés où la continuité
  linguistique devient nécessaire. Leur méthode sans entraînement obtient 88 %
  d'exactitude macro sur le sous-ensemble multicolonne OmniDocBench, contre 75 %
  pour XY-cut, mais le domaine et l'unité ligne diffèrent de nos régions de presse.
- Spécification primaire OCR-D PAGE, code/documentation consultés le 27/09/2026 :
  https://github.com/OCR-D/spec/blob/master/page.md. Elle représente les colonnes
  comme groupes ordonnés, potentiellement imbriqués, et exige que les images
  PAGE restent reliées au METS. Cela motive une projection relationnelle plutôt
  qu'un simple ordre implicite du XML.
- Eynollah actuel consulté le 27/09/2026 :
  https://github.com/qurator-spk/eynollah. Il propose ordre heuristique ou modèle
  entraîné, bornes de nombre de colonnes et PAGE-XML ; sa release 2025 ajoute un
  modèle d'ordre et du regroupement top-to-bottom. L'installation tire ONNX/
  TensorRT/CUDA et cible Python 3.8–3.11. Aucun gros paquet n'a été installé :
  le défaut mesuré était déjà résolu par 60 lignes de géométrie CPU testable.
- TextBite, dépôt primaire consulté le 27/09/2026 :
  https://github.com/DCGM/textbite-dataset. Ses 8 449 pages historiques annotent
  segments et relations dirigées ; c'est un futur candidat bien plus divers pour
  l'ordre/logical segmentation, mais son téléchargement complet fait 11,7 Go et
  n'était pas justifié pour ce test ciblé.

Sur les quatre pages développement Spiritualist, la convention distribuée est
strictement colonne gauche→droite puis régions haut→bas. Six seuils de rupture
horizontale ont été comparés ; `gap_ratio=0.14`, exclusion haute `0.055` et
largeur d'ancrage maximale `0.55` obtiennent 100 % macro et minimisent le nombre
de colonnes parmi les ex æquo. Paramètres figés avant ouverture de 0014.

Validation 0014 : 378/378 paires (1,000), contre 0,791 pour le tri global y→x et
0,794 pour x→y, 32 régions, 3 colonnes inférées, moins d'une milliseconde CPU et zéro passe
VLM. C'est un résultat positif mais conditionné aux régions distribuées et à une
référence d'ordre non adjudiquée. Il ne couvre ni détection, ni flux entrelacés,
ni SSU/articles. Conséquence architecturale : réserver le VLM aux ambiguïtés
sémantiques et utiliser la géométrie pour le cas colonnaire sûr. La proposition
brute ordonne encore quatre régions exclues par la référence ; un filtre de rôle
validé est obligatoire avant promotion dans le graphe.

## A05 — séparer ordre physique et structure sémantique

- Gabay et al., *SegmOnto: A Controlled Vocabulary to Describe and Process
  Digital Facsimiles*, JDMDH 2024, article et documentation primaires consultés
  le 27/09/2026 : https://doi.org/10.46298/jdmdh.12689 et
  https://segmonto.github.io/. SegmOnto privilégie une typologie physique,
  générique et contrôlée afin de mutualiser les données et de préserver le lien
  fac-similé → ALTO/PAGE → formats DH. Cela déconseille de confondre directement
  une classe physique avec un article éditorial.
- Gutehrlé & Atanassova, *Processing the Structure of Documents: Logical Layout
  Analysis of Historical Newspapers in French*, arXiv:2202.08125, texte intégral
  consulté le 27/09/2026 : https://arxiv.org/abs/2202.08125. Le papier distingue
  analyse physique et logique, part d'ALTO, et obtient sur son corpus français
  de meilleurs rappels avec des règles qu'avec RIPPER/Gradient Boosting. Son jeu
  de labels Text/Title/Header/Other et son annotation par une seule personne ne
  constituent pas une vérité article pour Spiritualist, mais confortent un
  hybride géométrie déterministe + classification sémantique.
- Mocaër et al., *Towards Hierarchical Structure Understanding of Newspaper
  Images*, arXiv:2607.15082v1, texte consulté le 27/09/2026 :
  https://arxiv.org/abs/2607.15082. Le papier 2026 formalise une hiérarchie
  METS/ALTO titre → sections → articles → blocs et compare une chaîne YOLO /
  LayoutReader / séparation custom à Tiramisu, modèle top-down multi-niveaux.
  Le dépôt public associé a été consulté mais sa vue GitLab ne livre pas de poids
  directement exploitables dans cette sandbox. Installer cette pile n'aurait pas
  résolu le défaut A05 isolé sans nouveau corpus adjudiqué.
- Code primaire NewsEye/CITlab consulté le 27/09/2026 :
  https://github.com/CITlabRostock/citlab-article-separation-new. Il forme un
  graphe de blocs à partir de 15 attributs de nœud et deux attributs d'arête,
  accepte séparateurs, similarité texte/BERT et indices de titres, puis regroupe
  par greedy/DBSCAN/linkage. Son environnement documenté repose sur Python 3.6
  et TensorFlow 1.12–1.14 ; il n'a pas été installé. Sa mesure splits/merges
  confirme qu'un F1 de paires doit être accompagné du nombre d'unités et des
  fusions/séparations.

Audit développement avant inférence : 86 régions, 32 SSU ; MASTHEAD/OTHER sont
toujours exclus du flux et HEADER/TEXT toujours inclus. Dix-sept SSU associent
HEADER+TEXT ; aucune SSU ne traverse une colonne dans ces quatre pages. Ces faits
ont été gelés comme convention provisoire, pas comme loi générale.

Une seule passe Luna sur la validation 0015 a produit une réponse brute valide.
Le filtre est exact (19/19 utiles, aucune contamination), les rôles valent 20/22
et l'ordre CPU après filtre 171/171 paires. La structure sémantique reste sous le
seuil : rappel de paires 0,917, précision 0,647, F1 0,759 ; B-cubed F1 0,870.
L'erreur dominante est une fusion de deux unités successives de la première
colonne ; deux relations de référence sont aussi manquées par l'affectation d'un
bloc au mauvais groupe. L'hypothèse suivante devra tester sur une nouvelle page
une contrainte « nouveau HEADER = nouvelle unité » ou un classifieur relationnel
local, jamais retuner puis revalider sur 0015.

## A06 — assemblage par titres et séparation des taxonomies

- Dell et al., *American Stories: A Large-Scale Structured Text Dataset of
  Historical U.S. Newspapers*, arXiv:2308.12477, texte intégral et dépôt officiel
  consultés le 27/09/2026 : https://arxiv.org/abs/2308.12477 et
  https://github.com/dell-research-harvard/AmericanStories. La chaîne est
  explicitement modulaire (layout/lignes, lisibilité, OCR, association). Les
  titres multi-boîtes, bylines et premier bloc article sont associés par règles
  de position ; le papier annonce 3,8 % d'articles multi-blocs et 0,2 %
  multipages dans son échantillon, et un F1 d'association de 97 sur 214 couples.
  Limites : presse américaine surtout antérieure à 1925, taxonomie et fréquence
  des cas complexes différentes, association évaluée surtout jusqu'au premier
  bloc ; ce n'est pas une validation de nos SSU Spiritualist.
- Barman et al., *Combining Visual and Textual Features for Semantic
  Segmentation of Historical Newspapers*, arXiv:2002.06144, texte consulté le
  27/09/2026 : https://arxiv.org/abs/2002.06144. Le signal OCR améliore de façon
  cohérente une base visuelle et la robustesse diachronique, mais la tâche est
  une segmentation sémantique pixel et non l'association article/flux. Pour
  BBVLM, cela justifie un futur routeur multimodal sur les ambiguïtés, pas une
  nouvelle passe VLM systématique.
- Palfray et al., *Logical segmentation for article extraction in digitized old
  newspapers*, arXiv:1210.0999, texte consulté le 27/09/2026 :
  https://arxiv.org/abs/1210.0999. Le système construit les articles à partir de
  séparateurs, titres et lignes et les stocke dans un wrapper METS relié à ALTO,
  avec indexation/correction au niveau article. Cela confirme que le genre et la
  structure logique doivent être projetés au-dessus des régions physiques.
- Mocaër et al., *Towards Hierarchical Structure Understanding of Newspaper
  Images*, arXiv:2607.15082v1, abstract et dépôt primaire consultés le
  27/09/2026 : https://arxiv.org/abs/2607.15082. Le papier compare une chaîne
  modulaire YOLO/LayoutReader/association custom à une architecture hiérarchique
  end-to-end. Il renforce l'intérêt d'une représentation multi-niveaux mais ne
  justifie pas d'installer ce gros système avant une référence adjudiquée.

Développement A06 : la règle locale figée « un `HEADER` ouvre une unité, sauf
chevauchement vertical avec un autre bloc de titre » passe de 0,9666 à 1,0000 de
F1 macro par paires sur 0009/0038/0041/0043 avec rôles oracle. Validation 0029 :
une réponse Luna valide, sans réparation, donne précision/rappel filtre
0,941/0,696, accord de rôle 0,630, F1 SSU 0,680 et rappel d'ordre 0,474.

L'audit visuel post-score montre un défaut de convention plus fondamental : cinq
des dix désaccords de rôle sont les deux encadrés publicitaires explicites. Luna
les appelle `ADVERT`; le corpus les code physiquement `HEADER`/`TEXT` et les
inclut dans l'ordre. Le gate reste négatif. La prochaine hypothèse doit séparer
trois axes — rôle physique, genre éditorial, appartenance à un flux — et conserver
les publicités dans METS/ALTO/retrieval même si elles ne font pas partie du flux
d'articles. Aucun appel Sol : il n'existe pas d'incertitude ponctuelle à arbitrer,
mais une incompatibilité de taxonomie et de cible mesurée.

## A07 — rôle physique, genre éditorial et flux indépendants

- Documentation et article SegmOnto consultés le 27/09/2026 :
  https://segmonto.github.io/ et https://doi.org/10.46298/jdmdh.12689. Le
  vocabulaire adopte une approche physique générique, ouverte à des sous-types
  sémantiques, afin de mutualiser les annotations et conserver le lien
  fac-similé → ALTO/PAGE → formats DH. Le dépôt d'exemples actuel a aussi été
  consulté : https://github.com/SegmOnto/examples. Limite : corpus surtout
  livres/manuscrits, pas une taxonomie éditoriale de presse validée.
- OCR-D Ground Truth Guidelines, régions PAGE et concordance METS/PAGE,
  consultées le 27/09/2026 : https://ocr-d.de/en/gt-guidelines/trans/lyTextregionen.html
  et https://ocr-d.de/en/gt-guidelines/trans/structurmets2page.html. PAGE possède
  une `AdvertRegion` explicite tandis que la structuration intellectuelle se
  projette dans la carte logique METS. `ADVERT` ne doit donc pas signifier
  automatiquement « texte à supprimer ».
- Schéma et tutoriel METS officiels de la Library of Congress consultés le
  27/09/2026 : https://www.loc.gov/standards/mets/mets et
  https://www.loc.gov/standards/mets/METSOverview.v2.html. METS distingue des
  `structMap` PHYSICAL et LOGICAL et relie leurs divisions à des fichiers ou
  segments. Il ne fournit pas seul un vocabulaire presse institutionnel.

A07 remplace le label unique par deux cartes complètes : rôle physique
`MASTHEAD/HEADER/TEXT/OTHER/UNKNOWN` et genre éditorial
`ARTICLE/ADVERT/NOTICE/MASTHEAD/OTHER/UNKNOWN`. Le logiciel, pas le modèle,
dérive le flux : HEADER et TEXT restent lisibles quel que soit leur genre.

Sur 0039, une passe Luna brute valide récupère exactement les 21 régions du flux
et l'ordre CPU obtient 210/210 paires. Le genre n'est pas scoré faute de
référence ; 21 régions sont proposées ARTICLE et trois MASTHEAD. Le gate échoue
néanmoins : 15/24 rôles physiques, F1 SSU 0,591. Cinq HEADER deviennent TEXT,
trois TEXT deviennent HEADER et un petit UNKNOWN devient HEADER. Le nombre
d'unités est correct (9), leurs frontières ne le sont pas.

Une calibration limitée aux quatre pages de développement sélectionne un seuil
hauteur/page de 0,020 ; avec appartenance grossière oracle, elle obtient F1 SSU
macro 0,969 et exactitude HEADER/TEXT 0,902. Cette valeur ne sera validée que sur
0044 ou 0050 ; 0039 est consommée.

## A08 — réduction du rôle et défaut de colonnes

Sources primaires revérifiées le 27/09/2026 : Gutehrlé & Atanassova
(https://arxiv.org/abs/2202.08125), Eynollah
(https://github.com/qurator-spk/eynollah), DocLayout-YOLO
(https://github.com/opendatalab/DocLayout-YOLO) et PERO
(https://github.com/DCGM/pero-ocr). Le premier motive l'hybride règles/modèles.
Eynollah offre régions, lignes et ordre mais sa pile actuelle vise Python 3.8–3.11
et peut tirer ONNX/TensorRT/CUDA. DocLayout-YOLO détecte des régions génériques,
pas les mots, l'ordre ou les articles. PERO fournit paragraphes/lignes/OCR et
PAGE/ALTO, pas la structure logique multi-colonne. Aucun de ces périmètres ne
justifie de présenter un poids générique comme solution sans mesure locale.

A08, une passe Luna, réussit STREAM (10/10), les 13 rôles fins et les quatre SSU
(F1 1,000). L'ordre reste 38/45 parce qu'A04 infère deux colonnes au lieu de
trois. Le défaut est géométrique ; un appel Sol ne l'arbitrerait pas. 0044 est
consommée. Le prochain test DocLayout-YOLO doit mesurer la couverture régionale
end-to-end, pas être présenté comme correction directe de cet ordre.

## A09 — détecteur exécuté et ordre robuste

DocLayout-YOLO 0.0.4, poids DocStructBench à la révision
`8c3299a30b8ff29a1503c4431b035b93220f7b11`, a été exécuté sur CPU sur la page
0044 consommée. Il couvre 95,9 % de l'union des régions et garde 97,3 % de sa
surface prédite dans la référence, mais sur-segmente : 25 prédictions pour 13
blocs, rappel one-to-one IoU≥0,5 de 0,538. Résultat positif pour la couverture,
négatif pour un remplacement direct des régions ALTO.

La correction d'ordre A09 filtre les ancres plus étroites que 2 % de la page et
affecte les régions par recouvrement avec les intervalles de colonnes. Le seuil
est choisi sur quatre pages développement avec un stress-test de ponts étroits ;
0050 obtient 36/36. Le défaut restant est un titre multi-ligne de 238 px : les
travaux de Gutehrlé & Atanassova motivent ici des règles combinant plusieurs
indices, plutôt qu'un simple relèvement du seuil de hauteur.

## A10 — typographie interne, sans nouvelle passe

Sources primaires relues le 27/09/2026 : Barman et al.
(https://arxiv.org/abs/2002.06144) montre sur des journaux historiques suisses et
luxembourgeois que l'ajout du texte au visuel améliore systématiquement une base
visuelle et la robustesse diachronique ; Palfray et al.
(https://arxiv.org/abs/1210.0999) reconstruit les articles à partir de titres,
lignes et séparateurs et les relie à METS/ALTO. Le dépôt officiel DocLayout-YOLO
(https://github.com/opendatalab/DocLayout-YOLO), relu à son état courant, reste
un détecteur générique à seuil de confiance et résolution d'entrée ; il ne
fournit pas à lui seul les unités sémantiques, l'ordre ou le profil METS.

Défaut visé : A09 utilisait la hauteur totale du bloc, donc un titre de deux
lignes pouvait ressembler à du corps. A10 utilise seulement des signaux déjà
présents dans ALTO : nombre de lignes, hauteur médiane de ligne normalisée et
proportion de capitales. Sur huit pages développement figées avant inspection,
180 combinaisons donnent au meilleur point F1 SSU macro 0,958 et exactitude de
rôle 0,989. La règle figée (≤2 lignes et hauteur ≥0,014 ou capitales ≥0,60)
obtient sur 0004 : rôles 1,000, F1 SSU 1,000, ordre 1,000. Limites : régions et
flux grossier sont oracle, la référence SSU est provisoire, une seule page est
consommée et aucun mot/texte n'est validé. Eynollah n'est donc pas installé à ce
stade : le défaut mesuré est corrigé localement sans sa pile plus lourde ; il
reste candidat si la détection ou le flux grossier échoue en bout-en-bout.

## A11 — une passe grossière, structure CPU figée

La page 0010 a été préparée avant lecture avec 15 jetons aléatoires ; le lecteur
ne voit ni XML, ni ordre, ni SSU. Luna rend les deux cartes complètes sans
incertitude et sans réparation. Les seuils passent : précision/rappel flux
0,917/1,000, rôles grossiers et fins 0,933, F1 SSU 0,857, ordre 1,000.

L'unique désaccord, audité seulement après le score, est une note éditoriale
lisible sur le télégraphe, source `OTHER/-1`, mais Luna `STREAM/NOTICE`. Cette
observation rejoint la séparation physique/logique de METS et les catégories
de région PAGE discutées en A07 : être exclu du flux principal ne doit pas faire
disparaître le texte de l'ALTO, des métadonnées ou du retrieval. Sol n'est pas
appelé car il n'y a ni rupture structurelle ni incertitude ponctuelle ; le
désaccord porte sur la convention et exige une politique/adjudication, pas un
vote de modèle.

## A12 — YOLO pour les colonnes, 27/09/2026

Sources effectivement lues : XY-Cut++ (14/04/2025), HTML §3.1–3.3,
https://arxiv.org/html/2504.10258v1 ; README officiel Eynollah,
https://github.com/qurator-spk/eynollah ; code officiel DocLayout-YOLO `demo.py`,
https://github.com/opendatalab/DocLayout-YOLO/blob/main/demo.py ; PERO
`pero_ocr/document_ocr/page_parser.py` sur la branche master officielle.
Les deux derniers fichiers bruts ont aussi été lus. Une tentative d'ouverture
d'un hypothétique `eynollah/utils/column.py` a échoué (404) : ce code n'a pas été lu.

XY-Cut++ distingue objets traversants et partition multi-granularité. Cela motive
des ancres de corps distinctes des titres et tableaux, sans prétendre implémenter
son algorithme. Eynollah produit segmentation, lignes et ordre PAGE avec options
de nombre de colonnes ; aucune inférence Eynollah n'a été exécutée. PERO permet
`DETECT_REGIONS=False` avec `DETECT_LINES=True` pour des régions fournies et
enchaîne layout, crops et reconnaissance. Alternative à comparer : détecter
les lignes sur la page entière puis les affecter aux colonnes, sans les couper.

Défaut mesuré : le rappel YOLO au bloc one-to-one pénalise sa granularité, sans
répondre à l'hypothèse de colonnes du projet. A12 réutilise les 25 détections
réelles de 0044, sans XML dans la construction : 3 colonnes retrouvées, 45/45
relations de même colonne correctes ; IoU des intervalles horizontaux
0,981/0,969/0,988. L'ordre conditionnel 45/45 utilise les y des régions source
dans l'évaluateur et n'est PAS un ordre détecté bout-en-bout. Les spans serrés
ne contiennent pas entièrement 142/415 rectangles de ligne source ; les tuiles
partitionnant la page 73/415, avec marge de 0,004 largeur/page 3/415. Les
rectangles source ne sont pas une vérité des pixels d'encre. Marge non retunée.
Coût : zéro nouvelle inférence, ~0,00023 s de post-traitement, détecteur déjà
mesuré à 2,36 s CPU. Une page consommée, aucune gate de réussite ouverte.

## A13 — lecture de paragraphes prédits, 27/09/2026

Complément primaire lu : README courant olmOCR-Bench,
https://github.com/allenai/olmocr/blob/main/olmocr/bench/README.md et présentation
des auteurs du 22/10/2025, https://allenai.org/blog/olmocr-2.
Le benchmark distingue présence de texte, ordre partiel, tableaux et formules,
avec relecture humaine ; ses règles normalisent ponctuation et suppriment des
en-têtes. Ces conventions ne conviennent pas telles quelles à notre conservation
diplomatique exhaustive. Nous retenons l'évaluation séparée des propriétés,
pas son score comme substitut au CER strict ni comme preuve de boîtes parfaites.
Pas d'installation olmOCR ni d'entraînement.

A13 échantillonne à graine fixe 3 détections plain-text de hauteur 80–260 px,
sans consulter le XML. Une passe Luna aveugle lit les crops natifs ; espaces
collapsés identiquement pour le score, sans normalisation de ponctuation.
Sol peut relire les blocs non exacts sans voir référence ni réponse Luna. Ce
routage par score est oracle-assisté et diagnostique, pas déployable tel quel.
Les résultats et désaccords restent dans `yolo-ocr-a13-0044/`.

Rectification de portée : A10 et A11 utilisent aussi les géométries de lignes
ET le texte distribués dans leur classifieur typographique. A11 remplace l'axe
grossier par une vraie lecture VLM, mais ni A10 ni A11 n'est une chaîne image
seule. Les scores précédents restent inchangés ; leur interprétation est limitée.

## A14/A15 — lignes entières et alignement, 27/09/2026

Relu : Kodym & Hradiš, *Page Layout Analysis System for Unconstrained Historic
Documents*, version du 23/02/2021, https://arxiv.org/pdf/2102.11838, sections
2.2–2.4 et 4. Le papier estime baselines, hauteurs et régions conjointement,
puis groupe les lignes. Il sépare évaluation géométrique et effet sur l'OCR.
Son hypothèse de hauteur constante par ligne ne garantit pas toutes les hampes.
Une première URL arXiv erronée (1910.09910, WeatherNet) a été écartée ; le HTML
2102.11838 était indisponible, le PDF a bien été lu.

Code courant officiel lu par téléchargement brut :
https://raw.githubusercontent.com/DCGM/pero-ocr/master/pero_ocr/document_ocr/page_parser.py
et https://raw.githubusercontent.com/DCGM/pero-ocr/master/pero_ocr/layout_engines/layout_helpers.py.
Le code installé 0.7.0 de `cnn_layout_engine.py`, `torch_parsenet.py` et
`core/layout.py` a aussi été inspecté. `assign_lines_to_regions` intersecte chaque
ligne avec toutes les régions candidates : avec régions recouvrantes, les
doublons sont donc possibles. Le moteur adaptatif peut faire deux forwards ;
le comptage A14 les mesure au lieu d'appeler arbitrairement cela une passe.

A14 isole l'assignation sur une seule détection réelle, paramètres inchangés :
416 lignes, 8 régions, 8,30 s CPU (4 threads), 2 forwards ; pas de nouvel appel
YOLO/VLM. Colonnes dures : 496 fragments, 80 lignes fragmentées. Colonnes avec
contexte : 635 fragments, 217 lignes fragmentées. Rattachement entier : 416,
aucune perte/duplication introduite ; 0,021 s. Toutes variantes : 385/418 lignes
source appariées à IoU≥0,5. Les 17 polygones tronqués de >1 % par l'assignation
native ne sont pas 17 erreurs OCR démontrées. Cette page est consommée.

A15 réutilise les lectures Sol A13 et les lignes A14, avec égalité stricte des
comptes par bloc avant liaison. Les 20 lignes reconnues une fois par PERO sont
ensuite alignées sur le texte VLM, sans nouveau VLM : 184 boîtes mot, texte
préservé, XSD valides. Le code natif utilise CTC, projection du crop et extension
locale ; absence de repli ne prouve pas que toute l'encre est encadrée. Les
overlays montrent notamment des tirets longs terminaux hors boîte. C'est le
prochain défaut géométrique à traiter, sans régler puis valider sur ces mêmes
crops. Cette intégration partielle ne compare pas les systèmes sur un test neuf.

## A16 — réparation additive de l'encre, 27/09/2026

Sources primaires effectivement lues : documentation API Kraken 7.0,
https://kraken.re/7.0/user_guide/api.html, qui décrit l'alignement forcé comme
produisant des positions de caractères et boîtes de mots approximatives ; Tang
et al., *Optimal Boxes*, ECCV 2022, https://arxiv.org/abs/2207.11934 ; Gupta et
al., *Automatic Assessment of OCR Quality in Historical Documents*, AAAI 2015,
https://ojs.aaai.org/index.php/AAAI/article/view/9600. Tang et al. montrent que
des boîtes géométriquement serrées ne maximisent pas nécessairement la lecture,
mais leur domaine scène/entraînement ne valide pas des ALTO de journaux. Gupta
et al. motivent un triage spatial de boîtes OCR bruitées, pas leur réparation
exacte. Deux chemins bruts Kraken supposés ont échoué à l'ouverture : aucune
affirmation de code source n'en est tirée.

Les périmètres actuels ont aussi été revérifiés dans les dépôts officiels.
Eynollah (https://github.com/qurator-spk/eynollah) couvre régions, lignes, ordre
heuristique ou appris et PAGE, avec une chaîne complète annoncée comme lente.
DocLayout-YOLO (https://github.com/opendatalab/DocLayout-YOLO) reste un détecteur
de régions. PERO (https://github.com/DCGM/pero-ocr) et le code A15 conservé sont
la base des positions mot. Ni Eynollah ni DocLayout-YOLO ne fournit ici une
référence indépendante de boîtes mot ; leur installation ne résout donc pas ce
défaut précis de ponctuation.

A16a assigne les composantes Otsu proches dans les cellules des mots : couverture
d'encre 89,953 % → 100 %, mais 179/184 mots changés et 30 849 pixels rectangulaires
ajoutés pour 5 212 pixels d'encre. Rejet pour surextension. A16b exige un
centroïde hors boîte : 72/184 mots, couverture 95,179 %, encore trop large.
A16c n'accepte ce candidat que si une ponctuation Unicode est au bord du token :
quatre changements, les deux `:—` visiblement tronqués inclus, couverture
90,105 %, aucun chevauchement voisin. Les trois variantes voient la page 0044
consommée ; l'audit visuel n'est pas une adjudication. A16c reste une proposition
de revue et aucun gate ne change.

## A17 — METS, MODS, PREMIS et image, 27/09/2026

Sources normatives effectivement lues : pages officielles Library of Congress
METS 1.12.1 (https://www.loc.gov/standards/mets/mets-schemadocs.html), MODS 3.8
et guide d'implémentation (https://www.loc.gov/standards/mods/userguide/), PREMIS
3 et exemples d'usage avec METS
(https://www.loc.gov/standards/premis/premis-mets.html), ainsi que l'explication
ALTO/METS (https://www.loc.gov/standards/alto/about.html). METS encode les
métadonnées descriptives, administratives et structurelles ; ALTO apporte le
contenu et les positions de mots, les pointeurs METS reliant les deux. MODS 3.8
est la version bibliographique courante et PREMIS 3 décrit Objets, Événements,
Agents, Droits et Entités intellectuelles.

Le schéma PREMIS 3 a été lu/téléchargé depuis le dépôt officiel
LibraryOfCongress/premis-v3-0 et validé par SHA-256. Le code METS 1.12 local a
également été relu : `FILEID` est un IDREF ; `digiprovMD` est prévu pour les
transformations OCR et les checksums acceptent SHA-256. Les pages officielles
MODS/PREMIS ont parfois répondu 403 à l'ouverture ; leurs résultats de recherche
et le dépôt PREMIS sont donc distingués des contenus réellement récupérés.

A17 ajoute sans inférence les groupes OCR, MASTER_IMAGE, DOCUMENT_GRAPH et
RETRIEVAL_INDEX. La page physique pointe vers image + ALTO. Trois payloads
locaux passent taille/SHA-256 ; l'image publique est comparée à l'empreinte A15
avant que son checksum soit déclaré ; tous les IDREF se résolvent. Quatre objets
PREMIS, un événement et un agent passent le XSD PREMIS 3. Le MODS ne contient
que l'identifiant local, car aucune notice indépendante ne justifie titre/date/
autorité. Le XSD MODS officiel reste indisponible (403), donc le rapport dit
explicitement `mods_3_8_xsd_valid=false`. Résultat positif d'intégrité, mais
aucun gate : validité XML et fixité ne prouvent aucune vérité documentaire.

## A18/A19 — référence externe et suppression réelle d'un étage, 27/09/2026

Sources effectivement lues pour cette hypothèse :

- Fiche primaire SBB/OCR-D-GT-VD-SBB, sections provenance, composition,
  curation et conventions : https://huggingface.co/datasets/SBB/OCR-D-GT-VD-SBB.
  Publication 31/10/2025, DOI 10.5281/zenodo.17395956 ; prestataire puis contrôle
  SBB et inspection manuelle page par page, 348 pages/67 ouvrages. La précision
  annoncée de 99,95 % n'est pas une garantie que notre échantillon est sans faute.
- Miroir officiel OCR-D : https://github.com/OCR-D/OCR-D-GT-VD-SBB, README,
  arbre, quatre XML et quatre TIFF réellement récupérés à la révision
  `481f7235acfc1f78e88b3c2f22f551595c3f2032`. Identités blob vérifiées.
  Le premier chemin supposé sous qurator-spk a échoué en 404, puis le dépôt
  réel a été résolu par recherche. La commande `hf` est absente ; le skill
  HF CLI a été consulté mais aucune installation n'était nécessaire pour ce miroir.
- Source BnF lue intégralement :
  https://api.bnf.fr/fr/ocr-corrige-de-documents-de-presse-de-gallica.
  Transcription manuelle et zones ; les lots internes/Europeana/IMPACT sont
  distincts de NewsEye. Les archives n'ont pas été téléchargées. Les recherches
  PRImA/ENP restent des pistes : pas d'annotation au mot contrôlée localement.
- OCR-D niveau 3 et ligatures :
  https://ocr-d.de/en/gt-guidelines/trans/tr_level_3_4.html,
  https://ocr-d.de/en/gt-guidelines/trans/trLigatur.html,
  https://ocr-d.de/en/gt-guidelines/trans/trLevels.html.
  Niveau 3 utilise Unicode puis MUFI/encodage convenu pour les glyphes absents ;
  le niveau n'est pas un sceau de qualité. Une conversion PUA improvisée pour
  réduire le CER serait une erreur de protocole.
- Kesidis et al., *A word spotting framework for historical machine-printed
  documents*, IJDAR 2011, PDF primaire, sections 3.2 et 6.1 effectivement lues :
  https://users.iit.demokritos.gr/~bgat/WordSpottingIJDA2011.pdf.
  Projections et RLSA complémentaires pour segmentation de mots, évaluation IoU.
  Domaine grec ancien imprimé et word spotting, pas preuve pour notre corpus.
  A19 teste seulement un mécanisme de projections avec abstention ; ce n'est
  ni une réimplémentation de l'article ni une méthode de segmentation nouvelle.
- Code primaire PERO courant effectivement lu :
  https://github.com/DCGM/pero-ocr/blob/master/pero_ocr/core/force_alignment.py
  et https://github.com/DCGM/pero-ocr/blob/master/pero_ocr/core/crop_engine.py.
  `force_align` prend des log-probabilités CTC ; le cropper calcule remapping et
  géométrie avec numpy/scipy/OpenCV. On peut réutiliser ce dernier sans reconnaître
  le texte, mais CTC n'est pas gratuit quand la reconnaissance manque.

Résultat A18 : 94 lignes/623 mots structurellement propres ; quatre panneaux
visuels source/candidat inspectés ; quatre autres ouvrages gelés non ouverts.
La lecture Luna révèle ambiguïté du crop incliné et conventions PUA, en plus
d'erreurs. Sol reprend seulement les dix incertitudes avec isolement polygonal.
Cette modification simultanée du lecteur et de la présentation est documentée,
pas présentée comme effet propre de Sol.

Résultat A19 : sans CTC, 50/94 lignes proposées, 294 mots émis, IoU moyenne
0,9453 mais neuf mots IoU<0,5 sur trois lignes malgré le filtre. Le rappel global
n'est que 0,4575. Sur 20 lignes prédites avec texte VLM déjà acquis, 18 passent
le filtre (pas de référence mot utilisable). Aucun paramètre retuné. Le prochain
routeur doit détecter ces mauvaises affectations avant d'ouvrir la réserve.
L'architecture et les ablations de valeur marginale VLM sont explicitées dans
`ARCHITECTURE_A19.md`. Une passe partagée texte/relations/preuves reste à tester,
pas un gain d'utilité déjà démontré.

## A20/A21 — lectures du 27 septembre 2026

OCR-D, table officielle OCR-D/IMPACT de codage :
https://ocr-d.de/de/gt-guidelines/trans/ocr_d_koordinationsgremium_codierung.html
et niveau 3 https://ocr-d.de/en/gt-guidelines/trans/tr_level_3_4.html.
Les descriptions confirment notamment F502=ligature ch, E42C=a avec e suscrit.
Le second n'est donc pas simplement ä dans une transcription diplomatique.
Code lu : fonctions de normalisation de dinglehopper, commit
1efb382a54c98cf2c6d716d134c57a2d1325a6b6, `src/dinglehopper/extracted_text.py`.
La normalisation SBB transforme aussi ponctuation et voyelles ; la voie MUFI
porte NotImplementedError. A20 ajoute des profils explicites et symétriques,
sans NFKC global ni transformation des exports. Détails, limites et empreintes
dans `conventions-a20/PROTOCOL.md` et `report.json` ; nouvelle inférence : zéro.

Groot & Valdenegro-Toro (TrustNLP, 21 juin 2024),
https://aclanthology.org/2024.trustnlp-1.13.pdf : introduction, méthode de
calibration, §4.2 et §5.1 lus. Leur petit jeu visuel et leurs anciens modèles
ne donnent pas une garantie pour l'OCR actuel. Ils motivent l'audit de confiance
A21 : toutes les six sorties Luna non incertaines sont relues en aveugle par
Sol, sans sélection individuelle par CER. Le routage courant ne teste que
le booléen uncertain ; son rappel d'erreurs doit être mesuré indépendamment.
Le résultat est une ablation de coût diagnostique, pas une politique validée.

Veille complémentaire : résumé primaire de Xuan et al., EMNLP novembre 2025,
https://aclanthology.org/2025.emnlp-main.74/ lu (pas le texte intégral).
Les auteurs étudient la calibration verbalisée multimodale et proposent un
prompt en deux étapes. Piste à comparer seulement si son coût marginal est
justifié ; ni méthode installée, ni gain transposé automatiquement à BBVLM.

A21 mesuré : Sol relit six lignes/12 images, améliore trois lignes et en
dégrade deux après décomposition. Le CER global gagne 0,95 point (6,11 % à
5,16 %), tandis qu'une ligne exacte est perdue. Rejeter la substitution
systématique et mesurer conjointement coût, gain et régressions ; ne pas
prendre l'accord de deux lecteurs comme adjudication.

## A22 — sources relues avant et après ouverture

Le README primaire `OCR-D/OCR-D-GT-VD-SBB` a été relu : 348 pages de 67
ouvrages, langues deu/fra/lat/nds, 1509–1827, transcription prestataire puis
post-correction SBB. OCR-D QA (`https://ocr-d.de/en/spec/ocrd_eval`) précise
GT représentative, CER/WER, espaces comme caractères, IoU, coûts CPU/wall/RAM
et nécessité d'une normalisation commune ; sa définition de caractère emploie
le graphème alors qu'A22 annonce explicitement ses points de code.

Documentation PAGE relue : `pc:WordType/Coords` est un polygone fermé, contenu
dans son parent ; les coordonnées référencent l'image racine. Glossaire OCR-D :
un mot est une suite de glyphes sans espace séparateur. Cela soutient l'IoU et
le dénominateur A22, sans certifier que chaque polygone source suit l'encre.

Après score seulement, la table officielle OCR-D a confirmé F519 « m with
tilde » (base m + U+0303) et F537 « ligature ta ». Ils expliquent une partie du
CER restant, mais ne sont pas injectés rétroactivement. Résultat expérimental :
4,86 % décomposé ; fast-path 7 boîtes toutes IoU≥0,8 mais 5,79 % de rappel.
La couverture 12,5 % contre 53,2 % sur développement interdit d'extrapoler
l'économie de CTC depuis A19. Aucun YOLO/Eynollah installé : le défaut mesuré
est au mot sous lignes oracle, pas un défaut de région/colonne.

## A23/A24 — CTC ciblé et ablation d'entrée VLM

Sources primaires et code officiel relus le 27 septembre 2026 :

- PERO OCR, dépôt officiel : https://github.com/DCGM/pero-ocr. Le README décrit
  un pipeline complet paragraphes/lignes/transcription, PAGE/ALTO, et précise
  que le modèle public est spécialisé sur les journaux tchèques microfilmés,
  même s'il vise l'imprimé européen. A23 épingle le paquet 0.7.0 et le SHA-256
  des poids 2022 ; il n'extrapole pas depuis le `master` courant.
- Kodym et Hradiš, *Page Layout Analysis System for Unconstrained Historic
  Documents*, ICDAR 2021, https://arxiv.org/abs/2102.11838. Article intégral
  lu : ParseNet prédit baseline, hauteur de ligne, limite de bloc et orientation.
  Ce n'est pas un détecteur de boîtes de mots conditionnées par un texte.
- Eynollah, dépôt et article primaire : https://github.com/qurator-spk/eynollah
  et https://doi.org/10.1145/3604951.3605513. Le code courant sépare layout,
  OCR et ordre de lecture ; régions/lignes et PAGE sont pertinents pour OLR,
  pas pour réparer directement les 14 lignes A22 sans boîtes de mots.
- DocLayout-YOLO, article et dépôt : https://arxiv.org/abs/2410.12628 et
  https://github.com/opendatalab/DocLayout-YOLO. Le modèle détecte des éléments
  de layout à 1024 px ; il ne fournit ni positions CTC ni boîtes de mots liées
  à une transcription. A12 l'a déjà testé comme ancre de colonnes.

A23 justifie donc l'installation PERO par un défaut mesuré. Sur les 16 lignes
A22 consommées, la passe CPU de reconnaissance prend 1,81 s, le réalignement
forcé 0,13 s. PERO natif donne 4,58 % de CER décomposé contre 4,86 % pour Sol :
sur ce petit domaine SBB, la passe VLM n'est pas encore justifiée par le texte
seul. Les boîtes forcées couvrent 121/121 mots mais seulement 7,44 % atteignent
IoU 0,8 ; le resserrement sur l'encre monte à 15,70 %, l'hybride à 19,83 %.
L'Otsu observé après score atteint 91,74 % à IoU 0,5 mais reste post-hoc.

A24 teste en une seule nouvelle tâche Sol un composite page entière + contexte
2x + ligne 4x. Il dégrade légèrement le CER : 11,62 % à 12,22 % strict, 4,86 %
à 5,01 % décomposé. L'échelle/contexte n'explique donc pas à elle seule le 0 %
Claude/Gemini rapporté. Une comparaison causale exige leurs entrées, prompt,
sorties brutes et convention de score exacts sur un nouveau lot commun.

## A25 — seuil d'encre après alignement CTC

Sources primaires et documentation officielle relues le 27 septembre 2026 :

- Nobuyuki Otsu, *A Threshold Selection Method from Gray-Level Histograms*,
  IEEE TSMC 9(1), 1979, DOI `10.1109/TSMC.1979.4310076`. La méthode choisit un
  seuil global à partir de l'histogramme ; elle ne fournit ni identité de mot,
  ni séparation, ni robustesse garantie aux fonds non uniformes. A25 lui donne
  donc des cellules issues du CTC et l'emploie seulement pour leurs extents.
- Kodym et Hradiš, ICDAR 2021, https://arxiv.org/abs/2102.11838, §1–2 relus.
  ParseNet apprend baseline, hauteurs, limites de blocs et orientation ; les
  auteurs distinguent explicitement extraction de lignes et binarisation. Leur
  résultat ne valide pas nos boîtes de mots CTC/Otsu.
- PERO OCR officiel, https://github.com/DCGM/pero-ocr, README courant relu. Le
  modèle public exécuté vise l'imprimé européen mais est spécialisé sur des
  journaux tchèques microfilmés ; cette spécialisation limite toute conclusion
  sur l'allemand ancien et, a fortiori, la presse française.
- OCR-D Ground Truth Guidelines,
  https://ocr-d.de/en/gt-guidelines/trans/, et documentation PAGE,
  https://ocr-d.de/en/gt-guidelines/trans/trPage.html. Elles établissent PAGE
  comme format annoté et permettent une validation technique ; elles ne
  transforment pas automatiquement une annotation de projet en vérité parfaite.

Résultat : `ctc_raw_otsu_v1` passe le critère agrégé local sur 1 097 mots
(rappel IoU≥0,5 99,45 %, IoU≥0,8 84,41 %), très au-dessus des boîtes PERO
natives (84,32 %, 16,77 %). Cela soutient l'architecture « CTC pour les
séparateurs, pixels pour les extents », pas une nouvelle méthode universelle.
Le lot est allemand et le code exact a été scellé après ouverture ; ces deux
limites empêchent toute promotion. Le lecteur Luna chargé de l'audit a en plus
signalé l'ambiguïté seuil-par-ligne/cellule, polarité, arrondis et coordonnées ;
l'interprétation exécutable est désormais consignée dans l'audit postérieur.

## A26/A27 — granularité de GT et structure logique de presse

Sources primaires et fichiers effectivement lus le 27 septembre 2026 :

- BnF, « OCR corrigé de documents de presse de Gallica »,
  https://api.bnf.fr/fr/ocr-corrige-de-documents-de-presse-de-gallica . La
  fiche annonce transcription manuelle, identification des zones et PAGE/XML ;
  le ZIP IMPACT a été ouvert après gel. Sa granularité observée est région,
  texte de région et ordre, jamais mot.
- Gutehrlé & Atanassova, *Processing the structure of documents: Logical
  Layout Analysis of historical newspapers in French*, 2022,
  https://arxiv.org/abs/2202.08125 . Le papier compare règles, RIPPER et
  Gradient Boosting sur ALTO français ; son meilleur rappel vient des règles et
  les auteurs proposent des hybrides. Il motive un post-traitement déterministe,
  pas l'assimilation d'un groupe PAGE à un article.
- Palfray et al., *Logical segmentation for article extraction in digitized old
  newspapers*, 2012, https://arxiv.org/abs/1210.0999 . Le pipeline construit
  les articles depuis séparateurs, titres et lignes, puis les sérialise dans un
  wrapper METS associé à ALTO pour la recherche. Cela motive la valeur d'une
  passe visuelle sémantique, mais ne fournit aucune preuve de score sur A27.
- Clausner et al., *The ENP Image and Ground Truth Dataset of Historical
  Newspapers*, ICDAR 2015, DOI `10.1109/ICDAR.2015.7333898`. ENP couvre régions,
  lignes, texte et ordre avec contrôle qualité, mais le niveau mot n'est pas
  documenté et le dépôt PRImA demande une inscription.

Conclusion expérimentale : un seul corpus public n'établit pas simultanément
boîtes mot, OCR, flux, articles et métadonnées. BBVLM doit conserver des gates
séparés : SBB français pour mots/CER ; BnF IMPACT pour régions/classes/OLR ;
adjudication distincte pour les articles. Le VLM A27 reçoit des IDs opaques et
doit résoudre les continuités inter-colonnes qu'une géométrie colonne-majeure
ne sait pas grouper, en une tâche visuelle réelle.

## A28 — conséquence expérimentale pour les boîtes

Le score scellé sur 1 753 mots français confirme la direction CTC+pixels mais
réfute sa perfection : IoU≥0,8 = 68,45 %. Le post-audit montre le défaut précis
qu'un nouvel étage devrait résoudre : la binarisation sur tout le rectangle de
ligne incorpore des composantes de ligne voisine et du bleed-through sur les
pages anciennes, surtout dans le catalogue en italiques. Un Otsu indépendant
par cellule n'améliore pratiquement pas le résultat (68,57 % à IoU≥0,8) ; cette
ablation négative est post-score et ne constitue pas une nouvelle validation.

La prochaine hypothèse documentée est donc un filtrage de composantes guidé par
la bande de baseline/hauteur de ligne, pas un autre détecteur de colonnes. YOLO
et Eynollah restent pertinents pour régions/colonnes/ordre, mais ne ciblent pas
ce défaut vertical au niveau mot. Toute variante doit être développée sur les
pages désormais consommées et validée sur une nouvelle source française.

Le diagnostic OLR A27 précise aussi le rôle du VLM : Sol atteint une précision
de paires de flux de 1,0 mais un rappel de 0,419, en sur-segmentant 6 des 13
OrderedGroups. Cela correspond à une politique d'abstention conservatrice : ne
pas fusionner sans preuve visuelle. L'hypothèse suivante n'est donc pas une
seconde passe VLM générale, mais un mergeur CPU de continuations inter-colonnes
sur les 34 flux proposés, avec routeur d'ambiguïté. Le gain doit être validé sur
une page non consommée ; A27 ne peut servir qu'au développement.

## A29 — continuités conservatrices en une passe

Sources primaires et code relus le 27 septembre 2026 : le dépôt Eynollah
(`https://github.com/qurator-spk/eynollah`) sépare explicitement segmentation,
OCR et ordre de lecture et propose ordre heuristique ou modèle. Les consignes
PRImA DMAS 2019 (`https://www.primaresearch.org/DMAS2019/resources`) encodent
chaque article comme groupe PAGE et rappellent qu'un article peut continuer
dans la colonne ou la page suivante. La recette IIIF Presentation 3.0
(`https://iiif.io/api/cookbook/recipe/0025-newspaper-article-index/`) représente
également ces fragments non contigus dans un Range ordonné. Ces sources
justifient une structure explicite, mais pas notre seuil numérique.

Le seuil A29 vient exclusivement d'A27 consommée : recouvrement horizontal
minimal 0,60 et interstice vertical maximal 0,007 largeur-page. Il ferme 34 en
13 flux et atteint F1 1,0 en développement, puis reste immuable. Sur la page
indépendante 00123453, Luna produit 17 flux ; le CPU les réduit à 15 pour 11
groupes de référence. F1 passe de 0,7132 à 0,7443, rappel d'ordre de bout en
bout de 0,5533 à 0,5918, contre F1 0,2277 pour la baseline géométrique avec
rôles oracle. Toutes les paires prédites restent correctes (précision 1,0),
mais le gate 0,90 échoue. Six régions de référence — surtout signatures,
source et deux publicités — ont été classées OTHER : c'est aussi un conflit de
convention éditoriale, pas seulement de géométrie.

Conclusion : le raccord CPU gratuit améliore réellement une passe Luna sans
fausse fusion, mais ne reconstitue pas encore toute la granularité PAGE. La
prochaine hypothèse doit apprendre/estimer une probabilité de continuation à
partir du gap, du changement de colonne, de la typographie et de la cohérence
textuelle déjà produite par la même passe, puis la tester sur un nouveau groupe
de pages. A29 est consommée et ne doit pas être retunée.

## A30 — ce que signifie réellement « 0 % CER »

Sources primaires consultées le 27 septembre 2026 :

- BnF, *OCR corrigé de documents de presse de Gallica*,
  https://api.bnf.fr/fr/ocr-corrige-de-documents-de-presse-de-gallica : la
  ressource annonce transcription manuelle, zones et PAGE/XML. Le contenu
  réellement ouvert confirme des textes de région français, mais aussi un
  caractère U+FFFD et des lectures probablement fautives ; « manuel » ne veut
  donc pas dire adjudication parfaite caractère par caractère.
- OCR-D, *Ground Truth Guidelines — Transcription*,
  https://ocr-d.de/en/gt-guidelines/trans/transcription.html : les conventions
  de transcription et la représentation Unicode font partie de la GT. Cela
  justifie le CER NFC diplomatique principal et une vue retrieval distincte,
  jamais la correction silencieuse de la référence.
- Liu et al., *OCRBench: On the Hidden Mystery of OCR in Large Multimodal
  Models*, 2023, https://arxiv.org/abs/2305.07895 : le benchmark couvre des
  tâches OCR variées, mais ne prouve pas 0 % de CER diplomatique sur presse
  française historique ni l'alignement aux conventions PAGE locales.
- Kiessling et al., *CHURRO: Benchmarking OCR-based Information Retrieval from
  Historical Documents*, 2025, https://arxiv.org/abs/2506.18763 : l'évaluation
  retrieval et l'évaluation diplomatique ne répondent pas à la même question.
  Une normalisation utile à la recherche ne peut donc pas remplacer le texte
  patrimonial conservé.

L'expérience A30 matérialise cette distinction. Sur les mêmes 3 004 caractères,
Luna vaut 1,7310 % strict et Sol 1,4647 % ; après normalisation de recherche des
tirets et césures, 0,8440 % et 0,5739 %. Les 24 substitutions Luna U+2011→ASCII
ne sont pas des mots mal lus mais restent des erreurs sous la convention gelée.
Inversement, `5e`/`3°` ou `Mme Faure`/`Mlle Fabre` restent des erreurs utiles à
mesurer après normalisation. Cette séparation doit être portée dans ALTO/METS :
forme diplomatique conservée, forme indexée dérivée et provenance de chaque
transformation.
# Ajout A32 — composantes et délimitation de l'encre (2026-09-27)

Sources effectivement lues, empreintes et extraits de code pertinents décrits
dans `component-boxes-a32/SOURCES.md` : Smith, Antonova, Lee (2009), sections
3.2–3.3; PERO `core/layout.py` actuel, export ALTO; Tesseract `makerow.cpp`
actuel, `dot_of_i` et `vigorous_noise_removal`. L'attachement des composantes
offre un complément CPU aux limites CTC, mais une suppression par taille seule
menace les signes détachés. A32 mesure trois ablations; le gain moyen ne suffit
pas, car des virgules/points disparaissent encore. Aucun nouvel outil lourd.
# Ajout A33 — ponctuation conditionnelle et petits contours (2026-09-27)

Le `tesseractclass.cpp` actuel a été lu : Tesseract sépare les seuils de petits
contours/ponctuation et expose des ensembles de signes initiaux/finals. A33 en
teste une version géométrique minimale, sans son classifieur. Résultat négatif :
la transcription seule ne révèle pas si le signe est déjà dans la boîte et
n'empêche pas de prendre du bruit voisin. Source, SHA-256, limites et copie des
octets dans `text-punctuation-a33/SOURCES.md`; aucun moteur lourd installé.

# Ajout A34 — audit de granularité des corpus (2026-09-27)

Sources primaires réellement lues : dépôts HTR-United DAHN et TAPUS, dépôt
OCR-D SBB, et article/dépôt Reichsanzeiger-GT. DAHN/TAPUS sont utiles pour la
transcription française au niveau ligne; Reichsanzeiger apporte 101 pages de
journaux corrigées deux fois. Mais les fichiers exemples inspectés n'encodent
aucun nœud géométrique `Word`. La littérature décrit parfois un volume en
« mots » alors que le format ne contient que des tokens dans le texte de ligne.
Cette distinction interdit de transformer une tokenisation en pseudo-GT de
boîtes.

La conséquence d'ingénierie est importante : les benchmarks OCR, layout et
OLR doivent rester complémentaires. Pour A34, seul SBB fournit la géométrie mot
requise; la sélection déterministe exclut tous les ouvrages déjà ouverts. Le
résultat indépendant confirme le bénéfice de composantes A32 mais rejette la
nouvelle règle de ponctuation. Sources, révisions, exemples et limites sont
consignés dans `word-transfer-a34/SOURCES.md`.


## A35: tested implication of CTC geometry and component attachment

2026-09-27: `scripts/evaluate_native_refinement_a35.py` applies unchanged A32 to cached native recognized words. On consumed French A28, recall IoU≥0.8 improves 11.07% → 80.66%; on consumed German/Latin A34, 19.04% → 55.96%. Reference transcription/token count are removed from the refiner; reference line rectangles and synthetic baselines remain. No new OCR/VLM inference or CER improvement. Joint exact-text+IoU≥0.8 recall is 73.25% / 42.09%, and visual audit confirms neighboring-ink/punctuation failures. All project gates stay false. See `experiments/loop/native-refinement-a35/RESULTS.md`, `SOURCES.md`, `PROTOCOL.md` and raw measurements. Next: predicted lines plus an unopened reference set, without retuning these consumed pages.

## A36 — predicted-line bottleneck

Current PERO master, Kodym & Hradiš (ICDAR 2021), Olejniczak & Šulc
(arXiv:2210.07903v2), pinned SBB GT and current DocLayout-YOLO scope were
re-read. With near-complete line detection, the measured defect is A32's
component ownership across tightly spaced lines, not missing macro-regions.
Exact revisions, hashes and negative evidence are in
`predicted-lines-a36/SOURCES.md`.

## A37 — frozen router validation

A37 introduces no new literature-derived hypothesis: it validates the unchanged
zero-parameter non-expansion guard on a newly frozen work, using the primary
sources and current code review already recorded for A36. Native mean word IoU
.568214 becomes .853595 and IoU80 recall .005085 becomes .686441, with gains on
every page. The result supports selective inexpensive geometry post-processing,
not a claim of perfect ALTO or a reason to add an unmeasured region detector.

## A38–A40 — ownership ablations

Current PERO 0.7.0 ALTO export code was inspected directly: word rectangles are
min/max crop coordinates of force-aligned CTC word spans with a fixed extension.
Official ALTO documentation defines String geometry but no pixel-ownership
algorithm. Historical segmentation work by Gatos et al. (IVC 2010) and
Louloudis et al. (Pattern Recognition 2009) treats punctuation, touching/broken
components, dense neighboring lines, and word gaps as coupled problems. Against
that background, three deliberately simpler rectangle-only rules were tested
and rejected on A28/A34/A36/A37: width non-expansion, vertical containment, and
equal-height translation rejection. Exact sources and results are in the A38,
A39, and A40 directories.

## A41–A43 — predicted line bands and connected-component ownership

Primary/current code inspected on 28/09/2026:

- `DCGM/pero-ocr@4301bdffe9205dff11579dae27b3f80458c27e89`, especially
  `pero_ocr/core/layout.py`: PAGE serializes each predicted baseline together
  with `heights_v2`; ALTO force-aligns the transcription to logits, maps the
  span through the crop grid, and emits min/max coordinates. These line-height
  estimates are therefore available without another model pass, but they are
  line geometry rather than word ownership truth.
- `cisocrgroup/ocrd_cis@a30ce3b033deddb70e7f18a479b2e5dc02bd4f26`,
  `ocrd_cis/ocropy/resegment.py`: the `ccomps` path propagates line seeds to
  connected components and resolves conflicts by majority label. Its processor
  targets line polygons and uses overlap safeguards; it does not validate ALTO
  word boxes or justify transplanting its thresholds.
- Likforman-Sulem, Zahour & Taconet, *Text Line Segmentation of Historical
  Documents: a Survey*, arXiv:0704.1267: neighbouring lines, degradation and
  interfering ink make line segmentation an open historical-document problem.

A41 translates PERO's local baseline/height band into a zero-parameter
non-worsening overshoot guard. A42 compares foreground pixels with predicted
line centres. A43 narrows that comparison to newly added foreground and uses
only a strict majority, following the qualitative `ccomps` idea without
copying its tuned processor parameters. On consumed A36/A37, A41 mean IoU is
.691499/.846076, A42 .689130/.851950 and A43 .696725/.853119, versus
.698075/.853595 for A37. Reduced regression counts do not compensate for lost
correct refinements. All three are rejected; no threshold is tuned post hoc.

## A44 — whole components, not pixel votes

The same current OCR-D CIS `ccomps` implementation motivated one narrower
test: assign each complete selected component to the majority-nearest predicted
line, then reject only a newly introduced foreign component. This is closer to
the cited processor's qualitative connected-component logic than A43, but it
still lacks OCR-D CIS's propagated seed labels. It halves many local regression
counts while lowering aggregate IoU, so it is rejected rather than thresholded
on consumed data.

## A45 — independent BnL reference

The Bibliothèque nationale du Luxembourg's current Open Data page was read on
2026-09-28. It declares pre-1878 newspaper OCR ground truth in German, French
and Luxembourgish, manually double-keyed to at least 99.95% transcription
accuracy. Its raw pack pairs uncropped blocks with ALTO and is explicitly meant
for testing/training text-line segmentation. This is stronger evidence for OCR
and lines than the flawed NewsEye references used earlier. It is not evidence
that every ALTO `String` rectangle was manually adjudicated, and 99.95% is not
zero reference error. A45 therefore separates OCR/line claims from word-box
claims.

## A46–A47 — ALTO units and audited residual transcription

Primary/current sources read on 2026-09-28:

- Library of Congress, ALTO technical centre and v4 schema documentation,
  <https://www.loc.gov/standards/alto/> and
  <https://www.loc.gov/standards/alto/techcenter/structure.html>. ALTO makes
  `MeasurementUnit` mandatory and locates it in `Description`; coordinates must
  be interpreted in that declared unit rather than assumed pixels.
- Bibliothèque nationale du Luxembourg, historical newspapers and METS/ALTO,
  <https://data.bnl.lu/data/historical-newspapers/> and
  <https://data.bnl.lu/data/historical-newspapers/mets-alto/>. Source TIFFs are
  documented at 300 PPI; the raw GT is intended for line segmentation and the
  transcription is double-keyed to at least 99.95%.

The sampled XML declares `mm10`. The standards-derived conversion to the
delivered 300-PPI raster is `300 / 254`, since one inch contains 254 tenths of
a millimetre. The first unscaled report is retained as invalid evidence; the
corrected report is an audited amendment, not a pristine first look. No source
claims manual adjudication of every `String` rectangle.

A47 tests whether known residual disagreements are visible transcription
errors. Luna and, only after escalation, Sol see opaque images without
reference alternatives. Agreement is a triage signal, not a ground-truth
construction rule.

## A48–A49 — page-level newspaper hierarchy (28 September 2026)

Mocaër et al., *Towards Hierarchical Structure Understanding of Newspaper
Images*, arXiv:2607.15082, was read in full together with the released Finlam
La Liberté dataset at revision
`c3d69ca1eef5a0f479b6aeaa6d6c155b3ec93657`. Its bottom-up system uses YOLO26
at 1024 px, LSD separators, LayoutReader and title-triggered article cuts. On
the authors' test it reports 72.27% block mAP@50, 80.39% article surface F1,
88.82% article mIoU and 87.20% block-order BLEU. Tiramisu instead uses four
hierarchical decoding passes and suffers cascading misses. These results
support separating physical detection/order from issue hierarchy; they do not
support perfect-box or zero-error claims.

Finlam rows contain normalized zone polygons, OCR-extracted text, semantic
classes, issue-logical order, article IDs and section IDs. A48 shows that a
continued article can precede the current page's masthead in `zone_orders`.
Palfray et al., *Logical segmentation for article extraction in digitized old
newspapers*, arXiv:1210.0999, likewise builds articles from separators, titles
and text lines and serializes hierarchy in METS alongside ALTO. Ha, Haralick &
Phillips, *Recursive X-Y Cut Using Bounding Boxes of Connected Components*
(ICDAR 1995), supports cheap whitespace/column analysis. Hakim et al.,
arXiv:2607.01018, further show that training-free semantic transition scoring
belongs after line nodes and geometry. BBVLM therefore assigns columns/local
order to geometry, and reserves one compact VLM pass for headline transcription,
editorial semantics, continuation cues and sourced metadata.

## A50 — semantic edges after geometric gating (28 September 2026)

Hakim et al., *Reading Order Inference for Complex Document Layouts*,
arXiv:2607.01018v1, was re-read in full. Their graph uses OCR-line nodes,
geometry-gated candidate edges, CLM conditional likelihood plus BERT NSP, and a
degree-constrained path cover. Sentence-embedding similarity does not help.
They report 88.0% macro edge accuracy on 140 multi-column OmniDocBench pages,
but only 74.2% on its newspaper subset versus 96.2% for XY-cut; semantic scoring
also costs 93.5 seconds/page on an A40 on average. Their stated limitations—OCR
noise, generic short fragments, semantic teleportation and need for typography
or visual cues—match the Finlam failure. This supports gating semantics after
cheap newspaper geometry, not replacing column detection with an all-pairs LM.

Current NewsEye/CITlab article-separation code was also inspected. It combines
separator detection, DBSCAN/alpha-shape blocks, heading/stroke features and a
GNN relation classifier; node features include block/baseline geometry and
heading indicators, edge features include separator crossings, with optional
visual and BERT similarities. This is closely aligned with A50’s measured need,
but the released stack targets TensorFlow 1.12–1.14 and trained models. Installing
it would not isolate a defect better than the current frozen Finlam experiment,
so no heavy dependency was added.

A50 therefore tests a smaller composition: recurrent geometry owns columns, a
cheap router selects only high-risk transitions, and one visual reader classifies
editorial continuity. On one consumed stress page it raises article-pair F1
.5869→.9093. Independent validation remains mandatory.

## Per-paper review ledger (28 September 2026)

Detailed paper-by-paper summaries, read scope, evaluated data, results,
limitations and BBVLM consequences now live in `PAPER_SUMMARIES.md`. This scan
adds Greif et al. 2025, Levchenko 2025, Archibald & Martinez 2025,
HIPE-OCRepair-2026, Hakim et al. 2026, Finlam/Mocaër et al. 2026 and Palfray
et al. 2012, plus the inspected CITlab implementation. Future reviews must add
one such entry per primary paper rather than only a cross-paper synthesis.

A51 falsifies the direct generalization of A50. On a reference-free frozen
router, one page improves but one page massively over-segments provider
articles; macro article F1 decreases .4876→.4823. The literature's recurring
message—physical cues constrain candidates, semantics can rerank, and
overcorrection requires per-unit non-regression—therefore applies to article
boundaries as well as OCR. The next ontology must separate provider containers
from retrievable semantic items.
