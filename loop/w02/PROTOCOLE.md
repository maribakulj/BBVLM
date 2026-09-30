# W02 — coupure entre deux mots choisie par Tesseract, bords gardés à l'encre

Figé le 2026-09-30 (~13h20 Paris) avant mesure.
Constat : BiedBern (O23) manque CRITERE à 94,74 % ≤ 0,5c ; les 9 frontières fautives tombent dans un petit blanc interne au mot au lieu du vrai blanc ; le placeur tourne en DTW seul (CTC absent, voir journal). Tesseract place ces coupures correctement (l. 1 : 708-734 = VT).
Règle : après le calcul des boîtes de mots (inchangé), pour chaque frontière k|k+1 dont les deux mots sont appariés à deux mots Tesseract consécutifs (`mots_tess.aligne`, psm 7, modèle de l'écriture déclarée), si notre séparateur (milieu du blanc entre nos boîtes) n'est pas dans le blanc Tesseract [droite(k), gauche(k+1)], la coupure est déplacée au milieu du blanc Tesseract : droite(k) = dernière colonne d'encre avant, gauche(k+1) = première colonne d'encre après ; hauteurs inchangées ; jamais au-delà des frontières voisines.
Mesure : CRITERE (C02b, S14) et txt+IoU80 sur les 52 pages, par page ; pire page.
Critère : adoptée si CRITERE total ne baisse pas, aucune page ne perd CRITERE, et la somme txt+IoU80 ne baisse pas ; toute page qui recule en txt+IoU80 de plus de 0,01 est examinée et rapportée.
