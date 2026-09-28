# O03 — consigne OCR-D niveau 2, pages jamais lues

Figé le 2026-09-28 avant lecture. Tirage déterministe (sha256("O03"+œuvre))
parmi les 53 œuvres SBB jamais utilisées ni par cette boucle ni par astra ;
première page de chacune des 4 premières : curineux_853804893/00000067,
helfkurt_829371303/00000126, betrdrzwt_648826694/00000060, ejngerez_821874276/00000020.

Lecteur : Opus, une passe, page réduite + bandes pleine résolution (la
configuration la meilleure d'O02 sur page dense). Deux lectures indépendantes
L1, L2 par page. Consigne = O02 + règles OCR-D niveau 2 citées : espaces
seulement entre mots, ponctuation collée au mot précédent ; folio, titre
courant, signature, réclame chacun sur sa propre ligne ; ornements non
transcrits ; e suscrit ≠ tréma ; J/I Fraktur selon le glyphe (J descend sous
la ligne de base). Post-traitement déterministe `outils/ocrd2.py`.

Mesure : CER diplo et norm contre la référence distribuée, puis adjudication
aveugle X/Y (`outils/adjuger.py`, arbitre Opus distinct) et CER contre la
référence adjugée (`outils/bilan_adj.py`). Réussite : 0 faute par page contre
la référence adjugée, en vue diplo, pour L1.
