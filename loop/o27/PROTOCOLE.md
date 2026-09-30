# O27 — validation de R6 (guillemet ouvrant collé) sur pages neuves

Figé le 2026-09-30 (~19h50 Paris) avant tout tirage, préparation ou lecture.

Motivation : R6 (L44 : règle OCR-D « guillemets collés au texte encadré » ; VT 36 « „x » / 0 « „ x ») a été écrite après avoir vu O26/buchdiss (5 lignes en échec « „ ␣mot »). Elle ne touche aucune ligne du dev : il faut des pages neuves qui contiennent le signe.

Tirage : œuvres de gt_pages.txt triées par sha256("O27"+œuvre), dernière page ni lue ni préparée ; on ne garde que les pages dont la VT (PAGE XML téléchargé, seule information consultée avant lecture) contient « „ » ; les 4 premières. La présence du signe est le seul critère ; le texte de la VT n'est pas autrement examiné.

Chaîne : celle du commit de ce protocole (R6 désactivée par défaut), lectures faites APRÈS génération complète des vues (zooms vérifiés), mesures CRITERE en série.
Hypothèse H-O27 : sur ces 4 pages, R6 activée (appliquée au texte final par outils/r4b.py, BBVLM_R6=1) contre R6 désactivée :
- texte glyphe (VT distribuée et adjugée A2) : total non supérieur, aucune page en hausse ;
- CRITERE : lignes en échec ≤, aucune page ne perd CRITERE.
Si tenu : R6 adoptée (défaut '1'). Sinon : rejetée.
