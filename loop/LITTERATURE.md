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
