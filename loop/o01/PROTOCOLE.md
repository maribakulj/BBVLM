# O01 — OCR texte brut pleine page par VLM Claude

Figé le 2026-09-28 avant toute lecture.

- Page : OCR-D-GT-VD-SBB @481f7235, borrdisc_689809840, OCR-D-IMG_00000018.tif
  (1315×2113), vérité PAGE niveau OCR-D, 27 lignes dont le folio.
- Lecteurs, à l'aveugle (aucune référence dans le contexte) :
  A — Opus, page entière réduite à 1350 px de haut ;
  B — Opus, page réduite + 5 bandes pleine résolution chevauchantes (600 px, 120 de recouvrement) ;
  C — Sonnet, mêmes vues que B.
  Une seule passe chacun (un appel d'agent, plusieurs images).
- Consigne diplomatique identique (ſ conservé, ligatures en lettres séparées,
  une ligne par ligne imprimée, folio inclus).
- Mesure : `outils/cer.py`, vues strict, diplo (ligatures MUFI décomposées),
  norm (diplo + ſ→s, tirets/apostrophes unifiés, espaces réduites).
- Critère de réussite : 0 édition en vue diplo. La vue norm est rapportée,
  pas substituée.
- Toute faute sera regardée sur l'image : faute du lecteur ou de la référence ;
  la référence n'est jamais modifiée.
