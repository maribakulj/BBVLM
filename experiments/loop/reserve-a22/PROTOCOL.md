# A22 — validation SBB réservée, protocole gelé avant ouverture

Gelé le 27 septembre 2026 avant tout téléchargement des quatre pages réserve.

## Hypothèses et entrées

- Une seule tâche `gpt-6-sol`, 16 lignes (4 par ouvrage) tirées uniquement par
  identifiant de ligne avec la graine 2026092722. Aucun Luna préalable, aucun
  routage par référence, aucune composition oracle de lecteurs.
- Cible polygonale blanche hors ligne, plus crop rectangulaire original comme
  contexte de glyphe ; Sol doit inspecter chaque cible. IDs opaques.
- Prompt A22 fixé : texte diplomatique visible, graphies/casse/ponctuation,
  ſ, ꝛ, abréviations ; ligatures lisibles décomposables ; e suscrit U+0364 ;
  incertitude explicite. Aucune référence ou ancienne prédiction accessible.
- CER strict et `glyph_decomposition_v1` figé par A20, points de code Unicode.
  Référence originale inchangée, aucune correction par accord de modèles.
- Géométrie : algorithme A19 inchangé, `min_gap_height_ratio=.10`,
  `gap_separation_ratio=1.5`, polygone de ligne oracle et texte Sol. Aucun CTC,
  logit ou boîte mot GT en entrée. Score IoU contre mots GT après production.

## Critères pré-déclarés

OCR : rapporter éditions, dénominateur, CER, lignes exactes et incertaines ;
zéro CER seulement si strict ET décomposé valent réellement zéro. La référence
SBB est institutionnelle et manuellement inspectée, mais les désaccords lisibles
restent à adjudiquer indépendamment.

Boîtes : couverture (lignes et mots), IoU moyenne des mots émis, rappel total
à IoU≥0,5/0,8, nombre de mots IoU<0,5 et lignes entièrement ≥0,8. Le succès
global exige à la fois absence d'erreur parmi les boîtes émises ET couverture
complète ; une abstention ne devient pas une boîte parfaite.

Coût : une tâche VLM, 16 cibles et contextes effectivement inspectés ; temps CPU
mesuré ; tokens/facturation `null` si indisponibles. Les images/XML, réponses
brutes, empreintes et paramètres sont conservés.

## Sources relues avant ouverture

- Dataset primaire SBB : https://github.com/OCR-D/OCR-D-GT-VD-SBB — 348 pages,
  67 ouvrages, 1509–1827, deu/fra/lat/nds, prestataire puis post-correction SBB.
- OCR-D QA : https://ocr-d.de/en/spec/ocrd_eval — GT représentative, normalisation
  commune explicite, lignes non appariées comptées comme erreurs.
- Code candidat local relu : `src/bbvlm/gap_alignment.py`, issu de l'ablation A19.
  Pas d'installation de YOLO/Eynollah : ce test vise le défaut mesuré de boîtes
  mot à partir d'un texte final ; ces outils de région/ligne ne le résolvent pas
  directement.

Cette réserve ne redevient jamais indépendante après ouverture. Aucun paramètre,
prompt ou profil ne sera retuné puis réévalué sur ces quatre pages comme holdout.

## Résultat — réserve désormais consommée

Sol a inspecté 16 cibles et 16 contextes dans une tâche, sans accès GT. CER
strict : 78/671 = 11,62 %, 1/16 ligne exacte. Après décomposition v1 figée :
34/699 = 4,86 %, 3/16 lignes exactes ; WER par tokens blancs 25/121 = 20,66 %.
Huit lignes sont signalées incertaines. Ce n'est ni 0 % ni une transcription
diplomatique parfaite. Les écarts incluent de vraies lectures, des ponctuations,
des e-suscrits rendus en umlauts et deux nouveaux codes PUA officiellement
documentés après score (F519 m tilde, F537 ligature ta). Ils ne sont pas ajoutés
rétroactivement au profil v1 de cette validation.

Le localiseur A19 accepte 2/16 lignes et 7/121 mots. Tous les 7 ont IoU≥0,8,
IoU moyen 0,971 et ont été inspectés dans l'overlay vert/violet. Rappel global
5,79 %. La précision conditionnelle parfaite sur sept mots ne prouve pas des
boîtes parfaites : quatorze lignes s'abstiennent. Couverture développement
50/94=53,2 % contre réserve 2/16=12,5 % ; Fisher bilatéral p=0,00262, signal
exploratoire de changement de domaine (petit n, lignes échantillonnées).

Décision : conserver la voie CPU comme fast-path haute précision ; fallback
CTC/PERO requis sur 87,5 % des lignes de cette réserve. Aucun réglage sur ces
pages. Le gain réel de calcul du fallback reste à chronométrer par lots.
