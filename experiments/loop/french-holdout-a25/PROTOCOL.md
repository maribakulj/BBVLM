# A25 — validation française indépendante des boîtes CTC/Otsu

Protocole figé avant téléchargement ou inspection des quatre pages du nouvel
ouvrage `briedefra_788606417`. La sélection utilise uniquement les chemins et
hashes du `tree.json` Git déjà conservé, à la révision
`481f7235acfc1f78e88b3c2f22f551595c3f2032` de `OCR-D/OCR-D-GT-VD-SBB`.

## Portée

Validation de géométrie conditionnelle : polygones de lignes et texte de
référence sont fournis. Ce n'est ni une mesure end-to-end, ni une validation du
texte VLM. Les quatre pages appartiennent au même ouvrage français et sont
indépendantes des huit ouvrages A18/A22, mais pas indépendantes entre elles.

## Candidat figé

1. PERO OCR 0.7.0, poids publics
   `pero_eu_cz_print_newspapers_2022-09-26`, CPU quatre threads, ParseNet coupé.
2. Chaque ligne source reçoit une baseline horizontale synthétique à 80 % de
   son rectangle, comme A23 ; une passe OCR met les logits CTC en cache.
3. Le texte de référence, après proxy NFC limité au codec, est aligné sur les
   logits. Le proxy ne modifie jamais le texte évalué/exporté.
4. Les milieux entre deux boîtes PERO forcées définissent les séparateurs.
5. Dans chaque cellule, un Otsu global est calculé uniquement dans le rectangle
   source de la ligne ; la boîte est l'enveloppe exacte des pixels d'encre de la
   cellule. Sans pixel, repli sur la boîte CTC.

Cette règle `ctc_raw_otsu_v1` a été observée après score sur A22 ; aucun seuil
n'est recalibré ici. A25 est son premier test figé sur de nouvelles pages.

## Mesures et critères

- appariement par index pour CTC forcé/Otsu lorsque le nombre de tokens égale
  le nombre de mots source ; sinon la ligne entière est comptée manquante ;
- PERO natif : appariement hongrois géométrique, avec tous les mots source dans
  le dénominateur ;
- IoU moyenne, rappel/précision aux seuils 0,5 et 0,8, nombre de lignes dont tous
  les mots dépassent 0,8, erreurs horizontales/verticales normalisées ;
- CER strict et `glyph_decomposition_v1` de PERO natif séparément ;
- temps de chargement, reconnaissance et réalignement CPU ;
- hashes Git blob et SHA-256, originaux inchangés.

Le candidat n'est promu que s'il améliore PERO forcé et PERO natif sur les
quatre pages sans omission. Même un succès reste conditionnel aux lignes et au
texte oracle et ne ferme pas le gate end-to-end.

