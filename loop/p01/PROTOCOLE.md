# P01 — seconde lecture sélective : signal a priori du désaccord lecture A / Tesseract

Figé le 2026-09-30 (~16h20 Paris) avant calcul.
Littérature : L27 (estimation de qualité OCR sans vérité terrain par accord entre moteurs).
Signal par page (sans appel VLM supplémentaire) : pour chaque ligne de la lecture A, distance d'édition normalisée (vue réduite) à la lecture Tesseract la plus proche parmi celles des lignes kraken de la page (cache `ancres_tesseract.json`, modèle de l'écriture déclarée) ; signal = moyenne sur la page.
Pages : toutes celles qui ont lecture A (p2_a), final (p3i/p3_final), référence adjugée auditée et cache Tesseract (O07-O25).
Politique « sélective » : seconde lecture + arbitre seulement pour le tiers des pages au signal le plus haut ; les autres gardent la lecture A (+ I01 comme en mode économe, non simulé ici : on prend p2_a).
Mesure : éditions (vue glyphe, adjugée auditée) sous trois politiques : A seule, sélective, complète ; corrélation de Spearman signal / gain (A − final).
Critère : P01 utile si la politique sélective garde ≥ 80 % du gain de la politique complète avec un tiers des secondes lectures.
