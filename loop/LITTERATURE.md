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
