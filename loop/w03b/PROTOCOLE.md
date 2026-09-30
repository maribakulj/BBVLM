# W03b — Calamari sur entrée binarisée, espaces appariées par rang

Figé le 2026-09-30 (12h03 Paris) avant mesure.
Constat W03 : sur niveaux de gris, Calamari met des espaces dans les mots et la règle « un seul blanc candidat » déplace des coupures loin (pire 5-13 c). Un test ponctuel sur ligne binarisée donnait une lecture parfaite. L29 : les modèles Calamari sont entraînés sur sortie nlbin (binaire) ; ocrd_calamari déduit aussi les mots des positions de glyphes, mais prévient que ces positions servent au surlignage, pas au traitement d'image.
Changement (BBVLM_W03=romain_b) : lignes recadrées binarisées (Otsu) avant Calamari (calamari_bin.json) ; espaces votées utilisées **seulement si leur nombre = nombre de frontières lues**, espace k → frontière k, déplacée vers le blanc d'encre qui contient l'espace (unique, entre le début du mot k et la fin du mot k+1), sinon inchangée. Romain seulement (le Fraktur garde W02) ; variante « tout_b » mesurée pour information.
Mesure : CRITERE (crit2/18/23/24/25, MODE=chaine2) sur les 60 pages, pire écart par page.
Adoption : CRITERE total ≥ 32/60 (actuel 31), aucun lot en recul, et aucune page dont le pire écart passe au-dessus de 2 c alors qu'il était en dessous.
