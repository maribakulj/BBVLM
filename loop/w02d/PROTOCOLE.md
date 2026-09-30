# W02d — W02 sur le romain avec le modèle d'écriture Tesseract `script/Latin`

Figé le 2026-09-30 (~16h40 Paris) avant mesure.
Constat : W02 avec le modèle de langue `lat` fait reculer le romain (W02 : −0,178 txt+IoU80 sur 21 pages ; O25 : W02c adoptée). Les modèles d'écriture tessdata_best (`script/*`) sont entraînés sur toutes les langues d'une écriture (documentation tessdata : « script » models), peut-être plus robustes à l'antiqua ancienne (ſ, ligatures, abréviations).
Règle testée : sur les pages déclarées romain, W02 appliquée avec `script/Latin` (au lieu de la désactiver, W02c).
Pages : les 25 pages en romain des lots O07-O25 (21 + 4 O25), **développement** (O25 a servi à W02c).
Mesure : txt+IoU80, taux ≤ 0,5c et CRITERE, sans W02 (état actuel) contre W02d.
Critère : si W02d fait mieux (somme txt+IoU80 et somme ≤ 0,5c plus hautes, aucune page ne perd CRITERE), validation obligatoire sur 4 pages neuves en romain avant adoption ; sinon rejet.
