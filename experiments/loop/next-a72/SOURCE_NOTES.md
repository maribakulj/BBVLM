# A72 — code et modèle effectivement inspectés

## Eynollah 0.9.2

- Code courant inspecté : wheel PyPI 0.9.2 et dépôt
  `qurator-spk/eynollah` au commit
  `15ddb7750e132462321a3d57b2a2b74cb8f2b151`.
- Fichiers/chemins lus : métadonnées de paquet, `eynollah.py` et son
  `do_prediction_new_concept`, `textline_contours`, configuration du model zoo.
- Paramètres reproduits : entrée 672×672×3, marge 10 % arrondie à 67 px,
  accumulation sigmoïde des recouvrements, classe ligne 1.
- Limite : BBVLM reproduit seulement l'inférence du modèle de lignes. Les
  heuristiques de contours, régions et ordre ne sont pas évaluées ici.

## Zenodo 21381102 — modèles Eynollah 0.9.1

- Type : dépôt officiel de modèles/code, **pas un article scientifique**.
- Version/date lue : record 21381102, publié le 15 juillet 2026.
- Archive : `models_training_layout_v0_9_1.zip`, 2,97 Go annoncés. Extraction
  par plages du seul SavedModel `modelens_textline_0_1__2_4_16092024` : six
  fichiers, 452 107 897 octets. Le bundle d'inférence ONNX a été consulté
  séparément et seul le modèle de lignes de 149 735 395 octets avait été extrait.
- Licence indiquée : CC-BY-4.0. Les SHA-256 des six fichiers sont figés dans le
  runner et vérifiés avant chaque inférence.
- Apport BBVLM : payer un étage pixelwise ciblé, non le pipeline Eynollah
  complet. Limite : le record ne certifie ni cette GT PAGE, ni l'ALTO final.

Le résumé séparé de l'article HIP 2023 de Rezanezhad et al. reste dans
`PAPER_SUMMARIES.md`, avec son niveau de lecture « abstract/métadonnées ».
