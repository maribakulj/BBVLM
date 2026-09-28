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
