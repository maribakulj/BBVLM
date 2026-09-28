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
