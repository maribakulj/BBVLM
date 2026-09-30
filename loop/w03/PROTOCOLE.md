# W03 — coupure entre mots par le CTC de Calamari (GT4HistOCR), bords à l'encre

Figé le 2026-09-30 (~17h25 Paris) avant installation et mesure.
Motivation : le placeur tourne sans son CTC (modèle kraken absent, zenodo bloqué) ; W02 (Tesseract) aide sur le Fraktur, nuit sur le romain ; L28 : Calamari + modèles GT4HistOCR (imprimé ancien, Fraktur et antiqua), accessibles.
Règle : même mécanique que W02 (w02.ajuste), mais les mots « externes » viennent de Calamari : ligne recadrée → prédiction (ensemble gt4histocr) avec positions des caractères → mots = suites séparées par une espace prédite, bornes = positions globales du premier/dernier caractère ; coupure déplacée seulement si notre séparateur n'est pas dans le blanc Calamari et si les deux mots sont appariés (distance ≤ 0,34).
Variantes mesurées : W03 sur toutes les pages (remplace W02 sur le Fraktur, s'applique au romain) ; W03 romain seulement (W02 gardé sur le Fraktur).
Mesure : txt+IoU80 et CRITERE sur les 60 pages (O07-O25) contre l'état actuel (W02c).
Critère : adoptée si CRITERE total ne baisse pas, aucune page ne perd CRITERE, somme txt+IoU80 plus haute ; et, si appliquée au romain, la somme sur le romain plus haute que sans W02 ; validation ensuite sur 4 pages neuves.
