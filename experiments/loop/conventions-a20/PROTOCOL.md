# A20 — profils d'évaluation, 2026-09-27

Hypothèse : une partie du CER A18 vient des conventions de transcription
de niveau 3. Définir les transformations à partir de sources, puis mesurer
symétriquement référence et hypothèse. Les 16 lignes sont déjà consommées ;
aucune sélection, correction des originaux ou ouverture de la réserve.

Sources réellement lues :

- OCR-D niveau 3 : https://ocr-d.de/en/gt-guidelines/trans/tr_level_3_4.html
- Table OCR-D/IMPACT : https://ocr-d.de/de/gt-guidelines/trans/ocr_d_koordinationsgremium_codierung.html
  HTML archivé. Attention, la colonne « Base » ne suffit pas pour décomposer
  une ligature : utiliser sa description, pas une suppression du second signe.
- Dinglehopper, code `src/dinglehopper/extracted_text.py`, révision
  `1efb382a54c98cf2c6d716d134c57a2d1325a6b6` :
  https://github.com/qurator-spk/dinglehopper/blob/1efb382a54c98cf2c6d716d134c57a2d1325a6b6/src/dinglehopper/extracted_text.py
  Fonctions normalize, unjoin_ligatures, substitute_equivalences lues ; source
  et licence Apache 2 archivées. NFC_MUFI n'est pas implémenté ; NFC_SBB effectue
  des substitutions plus larges que la décomposition des ligatures.
- MUFI v3 : résultat primaire indexé pour F1E8, « punctus interrogativus
  horizontal tilde ». Le PDF direct renvoie 404 ; ce signal n'autorise pas à
  assimiler automatiquement ce signe à '?'. F1E8 reste inchangé.
  https://mufi.info/mufi/pdfs/MUFI%20v3.0%20chart.pdf

Trois profils versionnés : strict, décomposition documentée, compatibilité
SBB reproduisant les dictionnaires épinglés (lecture AST, sans exécution du
code téléchargé). Le profil décomposé conserve ſ, ꝛ, ponctuation, abréviations
et e suscrit. Même lui perd l'identité graphique des ligatures : il ne remplace
pas le contrôle diplomatique de niveau 3. Le profil SBB est explicitement
avec pertes ; son remplacement q& est marqué douteux en amont.

Unité : points de code Unicode, espaces et ponctuation inclus. Le dénominateur
change avec les décompositions. Ce n'est pas le CER par graphèmes du programme
dinglehopper, ni une amélioration du modèle. Aucun changement de texte exporté.

Résultat : Luna 354/707 (50,07 %) strict, 311/736 (42,26 %) décomposé ;
Luna+Sol ciblé 92/707 (13,01 %) strict, 45/736 (6,11 %) décomposé.
Compatibilité SBB : respectivement 305/733 (41,61 %) et 39/733 (5,32 %).
Ni zéro CER, ni preuve indépendante de supériorité. Coût supplémentaire :
CPU seulement, aucune nouvelle lecture VLM pour A20. Les empreintes source,
implémentation, référence et réponses sont dans report.json.
