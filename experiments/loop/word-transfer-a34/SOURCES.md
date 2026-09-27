# Sources lues pour A34

Consultées le 27 septembre 2026. Les exemples de schéma cités ci-dessous ont
été inspectés avant le choix du nouvel ensemble; ils étaient exclus du score.

- OCR-D, `OCR-D-GT-VD-SBB`, révision
  `481f7235acfc1f78e88b3c2f22f551595c3f2032`. Source primaire des PAGE/TIFF.
  C'est le seul corpus inspecté ici qui encode effectivement des polygones
  `Word`. Les douze pages A34 proviennent de trois œuvres jamais ouvertes par
  A18/A25/A28 et leurs blobs Git sont vérifiés.
- HTR-United/DAHN, dépôt primaire : corpus français dactylographié, segmentation
  manuelle et transcription complète. L'exemple exclu
  `FRAD072_12J381_lettre0001_001.xml` contient des `TextLine`, mais un seul
  `String` par ligne et aucun `Word`/`Glyph`; il est impropre à l'IoU mot.
- HTR-United/TAPUS, dépôt primaire : 154 couples image/ALTO français provenant
  notamment de Gallica/Europeana. L'exemple exclu
  `12148-btv1b10581912k/16_7e494_default.xml` est lui aussi au niveau ligne.
- Neudecker et al., *The Ground Truth for the German Newspaper Portal*, source
  primaire Reichsanzeiger-GT : 101 pages historiques, correction humaine en
  double passe et 490 679 tokens annoncés. L'exemple PAGE exclu
  `1820_84_0220.xml` contient 260 `TextLine` mais zéro nœud `Word`/`Glyph`.
  Le terme « words » décrit donc des tokens de transcription, pas des boîtes.

Conclusion de sélection : ni la langue française, ni une transcription manuelle,
ni un comptage de mots ne prouvent l'existence d'une vérité terrain géométrique
au niveau mot. Le schéma réel doit être audité avant tout benchmark de boîtes.
