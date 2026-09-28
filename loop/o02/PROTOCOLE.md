# O02 — généraliser la lecture Opus pleine page

Figé le 2026-09-28 avant toute lecture. Pages jamais montrées à un lecteur de
cette boucle (SBB @481f7235, préparées par `outils/prep_sbb.py`) :

| page | écriture | lignes | caractères réf. |
|---|---|---|---|
| borrdisc_689809840 / 00000019 | romain français ~1770 | 28 | 1091 |
| drabnota_771639139 / 00000389 | Fraktur allemande | 29 | 873 |
| goskeinf_781556694 / 00000032 | Fraktur allemande (+latin) | 33 | 1538 |
| actevedef_718448162 / 00000024 | Fraktur, page dense 2463×4060 | 68 | 4430 |

Lecteurs Opus à l'aveugle, une passe chacun, consigne diplomatique unique
(ſ, ⸗, e suscrit U+0364, ligatures en lettres séparées, abréviations non
développées, aucune espace autour des traits d'union) :
- A1, A2 : deux lectures indépendantes de la page entière réduite (1350 px de haut) ;
- B : page réduite + bandes pleine résolution, sur les deux pages les plus denses.

Mesures (`outils/cer.py`, vue norm étendue avant lecture : ⸗→-, e suscrit→tréma) :
CER par page en strict/diplo/norm ; accord A1/A2 comme détecteur sans référence
(précision/rappel des lignes en désaccord vis-à-vis des lignes fautives).
Toute faute diplo est adjugée sur l'image : lecteur ou référence.
Réussite : 0 faute de lecteur adjugée par page, en vue diplo.
