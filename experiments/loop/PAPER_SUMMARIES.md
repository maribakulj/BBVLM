# Primary-source paper summaries

This file is the per-paper companion to `LITERATURE.md`. Every new literature
iteration records what was actually read, the evaluated data, the main result,
the limitation, and the concrete consequence for BBVLM. Search snippets are
never treated as if the full paper had been read.

## Scan of 2026-09-28

### Greif, Griesshaber & Greif (2025) — *Multimodal LLMs for OCR, OCR Post-Correction, and Named Entity Recognition in Historical Documents* — arXiv:2504.00414

- **Read:** arXiv abstract/HTML metadata and the paper's reported task/result
  summary.
- **Data/task:** German city directories from 1754–1870; direct OCR,
  multimodal OCR post-correction, and NER/structured extraction.
- **Advance:** multimodal post-correction combines the scan and an OCR
  candidate and reports consistently sub-1% CER without preprocessing or
  fine-tuning. It also extracts entities into structured records.
- **Limit:** sub-1% is not 0%; the domain is directory-like rather than
  multi-column French newspapers; the result does not provide ALTO boxes or
  article-level OLR.
- **BBVLM consequence:** a VLM pass is better justified as a joint constrained
  reader and semantic extractor given image + cheap OCR than as a replacement
  for deterministic layout. Compare direct reading and image+candidate
  correction on the same frozen crops, and keep entity evidence/provenance.

### Levchenko (2025) — *Evaluating LLMs for Historical Document OCR: A Methodological Framework for Digital Humanities* — arXiv:2510.06743

- **Read:** arXiv abstract and metadata; the full experimental appendix was not
  parsed in this iteration.
- **Data/task:** 18th-century Russian Civil-font material; 12 multimodal LLMs;
  contamination/stability protocol and historical-character metrics.
- **Advance:** exposes “over-historicization”: models can insert plausible but
  period-inappropriate archaic forms. It reports that post-correction can
  degrade transcription and argues for stability and contamination controls in
  addition to CER.
- **Limit:** different script/language and no newspaper article segmentation.
- **BBVLM consequence:** report diplomatic, search-normalized and
  interpretation layers separately; retain the immutable scan and reference;
  score repeated-reader stability and historical-character preservation rather
  than optimizing a single normalized CER.

### Archibald & Martinez (2025) — *Improving MLLM Historical Record Extraction with Test-Time Image Augmentations* — arXiv:2509.09722

- **Read:** arXiv HTML, including method, data size, qualitative error analysis
  and conclusion.
- **Data/task:** 622 Pennsylvania death records. Gemini 2.0 Flash reads many
  padded, blurred and warped variants; an adapted Needleman–Wunsch aligner
  fuses predictions and estimates confidence.
- **Advance:** about four percentage points better field accuracy than a single
  pass; padding and blur help accuracy, while warps expose uncertainty.
- **Limit:** many model calls (up to 100 augmentation configurations in one
  analysis), forms rather than newspapers, and even unanimous predictions can
  disagree with the ground truth.
- **BBVLM consequence:** do not adopt a costly augmentation ensemble as the
  default. Use a cheap image-quality router and reserve a second view/pass for
  ambiguous crops. Agreement is a review signal, never ground truth.

### Ehrmann et al. (2026) — *HIPE-OCRepair-2026: LLM-Assisted OCR Post-Correction for Historical Documents* — arXiv:2607.08143

- **Read:** full 17-page arXiv paper text, with focus on curation, scoring,
  systems, results and limitations.
- **Data/task:** English/French/German historical newspapers and books,
  17th–20th centuries; coherent paragraph/article units; text-only correction
  without images. Development and test references were manually revised and
  harmonized. Scoring is deliberately retrieval-oriented/semi-diplomatic.
- **Advance:** reproducible multilingual benchmark and scorer; best
  BnF-Mistral result is cMER 0.0040 on ICDAR2017 French versus 0.0184 for the
  uncorrected baseline. The paper adds an item-level preference score so large
  gains cannot hide many degraded units.
- **Limit:** text-only post-correction cannot adjudicate the scan; 0% is not
  reached; overcorrection remains important on low-noise inputs. Results measure
  search-oriented restoration, not exact diplomatic transcription or layout.
- **BBVLM consequence:** adopt the official French test data/scorer as an
  external normalized-OCR benchmark, while keeping strict/diplomatic metrics
  separate. Add per-unit non-regression and abstention gates. Because BBVLM has
  images, ambiguous corrections must be visually grounded.

### Hakim et al. (2026) — *Reading Order Inference for Complex Document Layouts* — arXiv:2607.01018

- **Read:** full arXiv paper text, including graph formulation, ablations,
  newspaper subset, runtime and failure analysis.
- **Data/task:** OCR text lines become graph nodes; candidate successor edges
  are scored with conditional language-model likelihood and BERT next-sentence
  prediction, then selected under degree constraints as a path cover.
- **Advance:** 88.0% macro edge accuracy on 140 multi-column OmniDocBench
  pages, and a maximum-regret inference strategy. Sentence embeddings do not
  improve the result.
- **Limit:** the newspaper subset reaches only 74.2%, below XY-cut at 96.2%; the
  reported pipeline averages 93.5 s/page on an A40. Generic continuations and
  cross-stream “semantic teleportation” remain failure modes; OCR noise was not
  tested.
- **BBVLM consequence:** semantics should rerank a small geometry-generated
  edge set, not construct physical order alone. Typography, separators and
  recurrent columns must stay in the CPU graph. A VLM/LM edge score needs
  explicit abstention and cannot justify one query per edge at production cost.

### Mocaër et al. (2026) — Finlam article-separation work — arXiv:2607.15082

- **Read:** arXiv paper/metadata and the Finlam task/corpus description already
  audited in A48–A51.
- **Data/task:** historical newspaper layout and article segmentation with
  provider article groupings and typed regions.
- **Advance:** supplies a large, structured source for testing columns,
  ordering, roles and article membership jointly rather than on isolated boxes.
- **Limit observed in BBVLM:** page 164 contains very large reference articles
  (173 and 67 zones). A visually coherent semantic splitter can therefore be
  scored as severe over-segmentation. Provider “article” is not automatically
  identical to an independently retrievable semantic item.
- **BBVLM consequence:** represent provider containers and semantic retrieval
  items as separate hierarchy levels. Do not train the latter directly on the
  former without an explicit mapping/adjudication protocol.

### Palfray et al. (2012) — newspaper structuring and METS/ALTO — arXiv:1210.0999

- **Read:** primary-paper metadata and method summary cited in the existing
  BBVLM literature audit; not re-read in full during this scan.
- **Advance:** an early explicit decomposition of newspaper processing into
  text lines, separators, titles, article structure and standardized output,
  rather than a monolithic OCR step.
- **Limit:** pre-VLM methods and older evaluation conditions; no evidence for
  frontier OCR accuracy or modern cross-domain generalization.
- **BBVLM consequence:** retain the staged physical/logical distinction:
  deterministic geometry and separators feed article inference, while METS
  links logical structure to ALTO rather than forcing semantics into word boxes.

## Current-code companion (not papers)

### CITlab article-separation repository (inspected 2026-09-28)

The current public implementation detects separators with ARU-Net, constructs
text blocks using DBSCAN and alpha shapes, detects headings, and predicts
relations with a graph neural network. Geometry, stroke statistics, heading
indicators and separators are first-class features; visual/BERT features are
optional. Its TensorFlow 1.12–1.14 stack is old, so it is useful as an
architectural reference rather than an immediate dependency. This directly
supports a hybrid BBVLM graph: cheap physical features first, one selective
semantic pass only where the graph is ambiguous.

## Competing-branch review (2026-09-28)

Before A51 interpretation, `claude/astra-branch-analysis-wf4gj4` was inspected
at its then-current two commits beyond `master`. Claude's O01 reports one Opus
page with zero adjudicated reading errors but one disagreement against the
immutable SBB reference (`oppoſer` versus reference `oppeſer`). It also reports
that page+band views were worse than the reduced whole page on this sample and
that Sonnet systematically confused long s. Their scorer separates strict,
diplomatic and normalized views and matches lines independently of reading
order. Their O02 protocol freezes four more pages, but no O02 result existed at
inspection time.

BBVLM will reuse the evaluation ideas (three views, per-page reporting,
reference adjudication) but not copy the unvalidated conclusion beyond that one
page. The two branches remain separate; future iterations must inspect Claude's
branch head before choosing a new hypothesis.

## A56 source summaries (restored to ledger in A57)

### Schultze et al. — Chronicling Germany, arXiv:2401.16845v4 (13 June 2025)

Read primary HTML dataset/annotation and pipeline sections. The revised body describes 801 German newspaper pages (1617–1933), 32,451 regions and 371,642 lines, whereas the abstract still says 693. Experts annotate region polygons; automatically initialized baselines/line polygons are only corrected for significant mistakes. Reading order is automatic and uncorrected. This supports independent region evaluation but does not provide certified word rectangles or reading-order truth. Code uses separate layout, baseline and OCR stages. For BBVLM, grade provenance by annotation layer, not by dataset name. Sources: https://arxiv.org/html/2401.16845v4 and https://github.com/Digital-History-Bonn/Chronicling-Germany-Code .

### Neudecker — Historical Newspapers Ground Truth (2019), Zenodo 2583866

Read primary record and parsed every released PAGE XML. The 50 Berlin State Library pages provide 2,458 text regions, 678 separators and region ordering, but no TextLine, Word or Glyph nodes. Creator strings are FineReader Engine 10; the record separately distributes FineReader 11 OCR. Manual word geometry is neither present nor documented. A56 rejects the corpus for word/line boxes and retains it as an OLR candidate. Source: https://doi.org/10.5281/zenodo.2583866 .

## A58 — complément Chronicling Germany
Article v4 https://arxiv.org/html/2401.16845v4 ; §§A.4.2/A.5.5 lus le 28 septembre 2026. Régions vérifiées par deux humains ; texte relu une fois, seconde correction annoncée. Signes zodiacaux/géométriques omis, fractions transcrites avec slash, espace nombre-unité. Lignes scindées conservées. Apport BBVLM : conventions et qualité doivent être distinguées par couche ; CER et ordre ne peuvent pas être certifiés à partir du seul label GT. Audit A58 : aucun Word XML, 801 pages, réserve100 pages, défaut de nom train documenté.


## A59 — veille complémentaire du 28 septembre 2026
- Inoue, *Context-Independent OCR with Multimodal LLMs: Effects of Image Resolution and Visual Complexity*, arXiv2503.23667v1 (31 mars2025), https://arxiv.org/html/2503.23667v1. Texte complet lu. 100 kanjis échantillonnés parmi2136, rendus à quatre tailles10/15/20/40px, GPT-4o/Gemini2.0 Flash/Azure. Les deux VLM déclinent à petite taille ; corrélation faible avec complexité. Limites : caractères synthétiques isolés, aucun journal ancien, pas Sol ; les seuils ppi ne se transfèrent pas à notre scan. Motivation pour A60 : ablation de taille visuelle sans changer les pixels source, pas preuve que la résolution explique déjà A59.
- Kiessling, *A Free Lunch? Adapting PP-OCRv6 for Historical Text Recognition*, arXiv2609.20064, 17 septembre2026. Abstract primaire retrouvé ; HTML/abstract direct indisponibles et HF404. Le résumé annonce un petit reconnaisseur de lignes, préentraînement hétérogène utile et comparaison à Medusa ; aucun score détaillé ni code lu. Candidat à examiner, pas à installer sur cette preuve partielle.
- *When Low CER is Not Enough*, arXiv2607.24077, 27 juillet2026 : abstract primaire retrouvé, texte non accessible dans cette session (HF404). Analyse d’hallucinations sur scans microfilms uruguayens. Pas de détail expérimental confirmé ; ne pas extrapoler au corpus BnL.


## A63 — sources relues le 28 septembre 2026

### Inoue — arXiv:2503.23667v1, 31 mars 2025
https://arxiv.org/html/2503.23667v1 ; méthodes/résultats/discussion relus. Cent kanjis synthétiques, quatre résolutions, GPT-4o/Gemini2.0Flash/Azure ; baisse des VLM à faible taille, complexité peu corrélée. Limites : glyphes japonais isolés, anciens modèles, aucune inférence sur Sol ni journaux luxembourgeois. A63 examine une présentation ciblée des pixels, sans prétendre récupérer de nouveaux détails ni isoler causalement la résolution d'une nouvelle session. Résumé détaillé déjà présent ci-dessus.

### Ehrmann et al. — HIPE-OCRepair 2026, arXiv:2607.08143
Relecture du dépôt de données et du README du scorer, pas nouveau téléchargement réussi du papier : arXiv abs/html/pdf renvoient DisabledError dans ce tour. Le résumé du texte complet lu au précédent tour est conservé tel quel.
Sources actuelles : https://github.com/hipe-eval/HIPE-OCRepair-2026-data et https://github.com/hipe-eval/HIPE-OCRepair-scorer . Version données v0.9.5 annoncée le20 avril2026 avec corrections GT après soumission. Le scorer calcule MER avec insertions au dénominateur ; sa normalisation conserve les accents, remplace ponctuation par espaces et compacte les blancs. **Ce n'est pas notre lexical_alnum**, qui supprime les séparateurs : ne pas appeler les scores interchangeables. Score de préférence par item pour rendre les régressions visibles. Pertinence : benchmark externe OCR normalisé, pas boîtes/OLR ni preuve de GT parfaite. Documentation relue, pas code Python du scorer exécuté dans A63.

Autres pistes repérées par recherche mais non lues intégralement : Beyene/Dancy2603.25761, comparaison2608.24976, cadre2510.06743. Aucun résultat ni choix d'implémentation attribué à leur seul extrait de recherche.

## A64 — lecture primaire logicielle, sans nouveau papier

### HIPE-OCRepair scorer 0.9.9 — code au commit d1e76e4

- **Lu :** code complet `ocrepair_eval.py`, README et métadonnées de paquet le
  28 septembre 2026 ; ce n'est pas une nouvelle lecture du papier.
- **Méthode :** normalisation ordonnée, alignement caractère jiwer, cMER micro
  et préférence +1/0/−1 par item contre le baseline.
- **Avancée pour BBVLM :** implémentation reproductible et vérifiée sur 64
  couples réels ; révèle 0,3004 % pour Luna brut contre 0,6346 % pour PERO sur
  A54, sans confondre ce chiffre avec `lexical_alnum`.
- **Limites :** aucune image, géométrie ou adjudication ; casse et ponctuation
  sont neutralisées ; un cMER nul ne serait pas une transcription diplomatique
  parfaite. A54 est consommé et ne redevient pas indépendant.
- **Code :** <https://github.com/hipe-eval/HIPE-OCRepair-scorer> ; révision
  exacte inscrite dans le protocole et le rapport A64.

## A65 — Schultze et al., Chronicling Germany, 2401.16845v4

- Version du 13 juin 2025, relecture du 28 septembre 2026 via HTML primaire
  et page HF markdown. Sections lues : 3, 4/pipeline, A.4.2, A.5 et A.7.2 ;
  il ne s'agit pas d'une nouvelle lecture intégrale de tout le papier.
- Méthode : régions par segmentation U-Net, détection séparée de lignes,
  puis reconnaissance LSTM. Les auteurs signalent la fragmentation des lignes
  aux frontières de classes et souhaitent dissocier frontières physiques et
  classes fines. Les régions ont un double contrôle humain, les lignes seulement
  une correction sélective. Ordre automatique ; articles encore à annoter.
- Apport A65 : ablation des masques oracle avant d'installer un détecteur.
  La fusion de tous les polygones texte ne résout presque pas les débordements
  observés ; le rectangle réduit les exclusions mais peut capter un voisin.
- Limites : désaccord géométrique entre deux couches d'annotation, pas preuve
  de perte d'encre ni de performance prédite ; aucune vérité d'article déduite.
- Sources : https://arxiv.org/html/2401.16845v4 et
  https://github.com/Digital-History-Bonn/Chronicling-Germany-Code .

### Code compagnon A65 (pas un article)
Arbre Git actuel 8a4b7c5613a888cde7d092e38b1841f3bff3f617, fichiers
`processing/slicing_export.py` et `yolo/preprocess.py` lus entièrement.
L'export optionnel masque sur label3/paragraph ; le prétraitement YOLO utilise
les rectangles englobants des polygones. Les variables width/height sont
inversées dans read_xml puis compensées dans convert_polygon_to_yolo : ne pas
qualifier ce seul nommage de bug de coordonnées. Aucun poids ni modèle testé
dans A65. Les niveaux de représentation doivent rester séparés dans ALTO/METS.

## A66 — lectures du 28 septembre 2026

### DocLayout-YOLO — Zhao et al., arXiv:2410.12628v1, 16 octobre 2024

Lecture du texte principal sections 1–5.3, pas de revendication de lecture intégrale
des annexes. Méthode : préentraînement par assemblage synthétique de documents
et champs réceptifs multi-échelles dans YOLOv10. Les sorties sont des éléments
documentaires, pas des colonnes garanties. Les évaluations mAP et vitesse ne
démontrent ni mots parfaitement encadrés ni CER nul en presse ancienne.
Apport BBVLM : candidat visuel léger déjà testé, réévalué ici sur cinq pages et
deux résolutions fixées, sans OCR ni PERO complet. Code officiel README et
`models/yolov10/predict.py` lus au commit 32a8ec276b3d79bf40561c4bc4b8e21ef32ac6fd :
filtrage de confiance puis retour aux coordonnées natives. Installation de la
version PyPI 0.0.4 ; prédicteur installé relu, chargement pickle explicite après
vérification SHA du poids public. Aucune extrapolation du débit GPU publié au CPU.
Sources : https://arxiv.org/html/2410.12628v1 ;
https://github.com/opendatalab/DocLayout-YOLO .

### Towards Hierarchical Structure Understanding of Newspaper Images

Mocaër et al., arXiv:2607.15082v1, 16 juillet 2026. Texte principal sections 1–8
lu (pas seulement abstract). Comparaison YOLO/LSD/LayoutReader/segmentation
d'articles et Tiramisu hiérarchique multi-passe. Le modèle ascendant obtient
72,27 % mAP50 et 80,39 % F1 articles sur leur protocole ; les erreurs amont
de Tiramisu peuvent supprimer tous les enfants d'un article. Limites cruciales :
publicités exclues, annotations Finlam imparfaites, OCR non gold, divergences de
granularité. Le BLEU de classes peut masquer des permutations entre blocs de
même classe ; cette dernière réserve est notre analyse de leur métrique.
Apport BBVLM : mesurer hiérarchie et contenu distinctement, ne pas traiter
Finlam comme certification CER. Code annoncé (non inspecté dans A66) :
https://git.litislab.fr/tiramisu/tiramisu-newspaper-articles-extractor ; évaluateur
https://gitlab.teklia.com/adr/newspaper/evaluation .
Source : https://arxiv.org/html/2607.15082v1 .

### Institutional Newspapers Pipeline — Cargnelutti et al.

arXiv:2608.18972, 19 août 2026. **Abstract seulement** : version précise du texte
complet non inspectée, récupération HTML indisponible. Pipeline modulaire avec
découpes indépendantes des types, OCR, classification, ordre, NER et embeddings ;
annonce un corpus dérivé de 1,47 million de scans. Intérêt pour BBVLM : séparer
découpe physique et typage, réutiliser une transcription pour plusieurs usages.
L'abstract ne permet pas de vérifier CER, adjudication, coût CPU ou conventions
des boîtes ; aucune performance n'est importée comme résultat BBVLM. Le code
et les modèles sont annoncés, mais aucun dépôt n'a été inspecté dans cette
lecture. Source : https://arxiv.org/abs/2608.18972 .

Autres résultats de recherche (TongGuOCR, survey OCR, Layout-Aware OCR in Black
Digital Archives) : repérage seulement, pas de lecture scientifique revendiquée.

## A68 — lectures du 28 septembre 2026

### Jiang, Hao & Liu — *Deep Scene Text Detection with Connected Component Proposals*

- **Version/date :** arXiv:1708.05133v1, 17 août 2017.
- **Niveau lu :** texte principal complet disponible en HTML, sections 1–5,
  méthode, entraînement, tableaux et discussion ; pas seulement l'abstract.
- **Méthode :** segmentation pixel-à-pixel et ligne centrale, propositions par
  composantes connexes, puis vérification par détection de caractères et perte
  de cohérence. Sur ICDAR 2013 scène, les auteurs annoncent rappel 0,915,
  précision 0,922 et F1 0,919.
- **Limites :** photos de scène modernes, boîtes mots/caractères supervisées,
  réseau entraîné ; aucune presse historique, colonne, ALTO, CER ou OLR. Une
  composante connectée reste une proposition, pas une propriété sémantique.
- **Code :** aucune implémentation officielle actuelle inspectée dans A68 ;
  aucun modèle installé.
- **Apport BBVLM :** tester un signal pixel local comme garde d'une boîte objet
  tout en mesurant séparément contamination et couverture.
- **Source :** https://arxiv.org/abs/1708.05133 .

### Sauvola & Pietikäinen — *Adaptive document image binarization*

- **Version/date :** *Pattern Recognition* 33(2), 2000, DOI
  10.1016/S0031-3203(99)00055-2.
- **Niveau lu :** abstract primaire et métadonnées seulement ; le texte
  intégral éditeur renvoyait HTTP 403 dans cette session.
- **Méthode annoncée :** seuil local adaptatif fondé sur les statistiques du
  voisinage pour bruit, illumination et dégradation de documents.
- **Limites :** aucun paramètre ou résultat du texte non lu n'est importé. A68
  utilise Otsu, pas Sauvola ; le seuillage global reste une hypothèse.
- **Code :** aucun dépôt officiel lu, aucune dépendance ajoutée.
- **Apport BBVLM :** garder la binarisation remplaçable et la valider sur une
  réserve diverse plutôt que l'assimiler à une vérité d'encre.
- **Source :** https://doi.org/10.1016/S0031-3203(99)00055-2 .

### Sukesh et al. — *A Fair Evaluation of Various Deep Learning-Based Document Image Binarization Approaches*

- **Version/date :** arXiv:2401.11831v1, 22 janvier 2024.
- **Niveau lu :** abstract primaire seulement ; l'ouverture du texte arXiv a
  échoué dans cette session.
- **Méthode annoncée :** comparaison commune de binariseurs profonds sur DIBCO
  2013/2017/2018/2019, avec code et modèles.
- **Avancée annoncée :** aucun modèle ne domine tous les jeux ; DE-GAN,
  DP-LinkNet, 2-StageGAN et SauvolaNet gagnent des sous-ensembles différents.
- **Limites :** l'abstract ne suffit pas à reproduire les scores et ne traite
  pas directement les bords de régions historiques.
- **Code :** https://github.com/RichSu95/Document_Binarization_Collection,
  non inspecté ni installé faute de défaut mesuré justifiant un gros outil.
- **Apport BBVLM :** Otsu reste une ablation légère, pas une règle promue avant
  transfert sur des pages diverses.
- **Source :** https://arxiv.org/abs/2401.11831 .

## Rezanezhad et al. — Document Layout Analysis with Deep Learning and Heuristics

- **Version/date :** HIP 2023, pp. 73–78, DOI 10.1145/3604951.3605513 ;
  consulté le 28 septembre 2026.
- **Niveau lu :** abstract primaire et métadonnées seulement ; texte ACM bloqué
  (403). Le README/code actuel Eynollah a été inspecté séparément.
- **Méthode annoncée :** segmentation pixelwise CNN des documents historiques,
  complétée par heuristiques pour marginalia et ordre de lecture ; comparaison
  sur trois jeux historiques.
- **Limites :** l'abstract ne donne pas les scores/tableaux reproductibles ; ne
  démontre ni boîtes ALTO parfaites ni CER nul. Le pipeline actuel est multi-
  modèle, lent et plus large que le défaut A70.
- **Code :** `qurator-spk/eynollah` head
  `15ddb7750e132462321a3d57b2a2b74cb8f2b151`, v0.9.2 ; segmentation de dix
  classes, lignes, régions et OLR, Python 3.8–3.11/ONNX.
- **Apport BBVLM :** alternative crédible de rappel pixelwise si l'audit A71
  confirme du texte visuellement manqué ; ne pas l'installer pour des divergences
  de convention.
- **Sources :** https://doi.org/10.1145/3604951.3605513 ;
  https://github.com/qurator-spk/eynollah .

### Note A72 sur l'implémentation et les poids (pas un nouvel article)

Le 28 septembre 2026, le code réellement pertinent d'Eynollah 0.9.2 a été lu :
`do_prediction_new_concept`, `textline_contours`, le model zoo et les métadonnées
du wheel. L'archive officielle Zenodo 21381102 (15 juillet 2026) a été inspectée
et seul le SavedModel de lignes a été extrait. Les paramètres reproduits, les
six SHA-256, la licence et les limites sont consignés séparément dans
`next-a72/SOURCE_NOTES.md`. Cette note ne change pas le niveau de lecture de
l'article HIP 2023 ci-dessus : abstract et métadonnées seulement.

## A73 — lecture du 28 septembre 2026

### Liebl & Burghardt — *An Evaluation of DNN Architectures for Page Segmentation of Historical Newspapers*

- **Version/date :** arXiv:2004.07317v2, version datée du 22 mars 2026 dans le
  texte HTML ; article initial de 2020.
- **Niveau lu :** texte complet HTML, sections méthode, génération de GT,
  configuration, tableaux et conclusion ; pas seulement l'abstract.
- **Méthode :** comparaison systématique de 11 backbones et 9 schémas de
  résolution/tuilage pour segmenter pixels de texte, tables, images/bordures et
  séparateurs du *Berliner Börsen-Zeitung*. Les folds sont définis par page et
  non par tuile ; MCC, IoU et exactitudes sont comparés.
- **Résultats :** Inception-ResNet-v2 et EfficientNet figurent parmi les meilleurs
  selon la tâche ; le tuilage vertical reste généralement proche du traitement
  entier. Les auteurs annoncent pour leurs modèles finaux blkx une mean-IoU de
  74,86 % à 92,67 % selon le fold et signalent que 24–41 pages atteignent 99 %
  de la performance du jeu complet selon la tâche.
- **Limites :** segmentation sémantique de régions, pas lignes/ALTO/CER/OLR ;
  GPU V100 et journal allemand unique. Les auteurs notent explicitement que la
  segmentation pixelwise peut fusionner accidentellement des régions voisines.
- **Code :** lien P2PaLA cité, mais aucun dépôt propre à cette étude n'a été
  inspecté ou installé dans A73.
- **Apport BBVLM :** mesurer la contamination et ne pas transformer une région
  dense en rectangle sans contrôle. A73 confirme empiriquement cette limite.
- **Source :** https://arxiv.org/abs/2004.07317 .

## A74 — relecture primaire du 28 septembre 2026

### Schultze et al. — *Chronicling Germany*, arXiv:2401.16845

- **Version/date lue ce tour :** texte intégral HTML v3, 25 octobre 2024. La
  version v4 du 13 juin 2025 et ses changements vers 801 pages étaient déjà
  lus et résumés en A56/A58/A65 ; les chiffres de versions ne sont pas mélangés.
- **Niveau lu :** texte complet v3, notamment composition, pipeline, baseline,
  généralisation et processus d'annotation ; pas seulement l'abstract.
- **Méthode :** régions polygonales PAGE, U-Net de baseline/ligne entraîné sur
  crops 256×256 avec objectif conjoint ligne/bloc, puis OCR séparé. Le jeu v3
  décrit 693 pages, environ 350 000 lignes et trois millions de mots.
- **Résultats :** F1 de baseline annoncé autour de 0,9 ; la généralisation du
  layout hors domaine reste insatisfaisante alors que l'OCR généralise mieux.
- **Limites :** aucune boîte texte GT, donc comparaison aux détecteurs d'objets
  jugée inadéquate par les auteurs ; transcription relue par un seul expert à
  ce stade et seconde correction annoncée ; forte dominante Kölnische Zeitung.
- **Code/données :** dépôts officiels Chronicling Germany liés par l'article ;
  A74 utilise la révision publique épinglée déjà vérifiée, sans nouveau modèle.
- **Apport BBVLM :** valide l'usage des lignes/baselines comme couche distincte
  et impose de ne pas appeler les polygones ligne une vérité de boîte parfaite.
- **Source :** https://arxiv.org/html/2401.16845v3 .

### Code Eynollah `separate_lines.py` (implémentation, pas un article)

- **Révision :** arbre `main` officiel
  `15ddb7750e132462321a3d57b2a2b74cb8f2b151` inspecté le 28 septembre 2026.
- **Lu :** projection de densité/lissage/pics-vallées, deskew local,
  `textline_contours_postprocessing`, `separate_lines_new2` et
  `do_work_of_slopes_new_curved`.
- **Limites :** branches et seuils historiques, besoin de régions parentes ;
  le pipeline complet n'est pas installé et aucun résultat ne lui est attribué.
- **Apport :** confirme qu'A73 a supprimé une étape essentielle en remplaçant
  directement chaque composante par son rectangle ; A75 doit tester une vraie
  séparation ligne plutôt que retuner les rectangles consommés.
- **Code :** https://github.com/qurator-spk/eynollah/blob/main/src/eynollah/utils/separate_lines.py .
