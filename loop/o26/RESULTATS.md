# O26 — résultats (4 pages neuves, chaîne du 30/09 19h30) — H-O26 TENUE (SR neutre hors réglage)

Écart de mise en œuvre (signalé) : 6 lectures (baltdiss, culmsent, buchdiss) lancées avant la génération des vues zoom → écartées (lectures/*_sanszoom.txt) et refaites avec les zooms, conformément à la chaîne. Les mesures CRITERE avec/sans SR ont d'abord tourné en parallèle en écrivant le même fichier intermédiaire → refaites l'une après l'autre (crit_sans_sr.log, crit_sr.log).

| page | car. | texte glyphe VT distribuée | texte glyphe adjugée (A2) | lignes exactes | CRITERE (avec SR = sans SR) | lignes en échec |
|---|---|---|---|---|---|---|
| 852691769/512 (tableau, latin) | 1057 | **0** | **0** | 53/53 | ✗ | 2 (titre vertical « Claſſis III… » ; « tis laminis in acu- » IoU 0,46) |
| baltdiss/27 | 2202 | 4 | 1 | 37/38 | ✓ | 0 |
| buchdiss/13 | 1594 | 35 | 11 | 20/26 | ✗ | 5 (les 5 lignes « „ ␣mot » : blanc après guillemet ouvrant) |
| culmsent/27 | 1269 | 6 | 2 (norm 0) | 33/35 | ✗ | 2 (VT « adi piſcitur » coupé ; « Ne quenquam punito… » sans candidate ≥ 0,5) |

- **H-O26 tenue** : lignes en échec 9 (avec SR) ≤ 9 (sans) ; aucune page ne perd CRITERE ; boîtes de ligne identiques dans les deux modes (0 boîte différente sur 155) → rappel de lignes identique. La SR n'a choisi que des lignes kraken d'origine sur ces pages (vérifié : l'interrupteur agit, euanaua 22 lignes avec SR contre 23 sans) : **neutre hors jeu de réglage**, ni gain ni recul. Ses gains du dev viennent de cas (titres coupés, lignes soudées) absents ici.
- Oracle D sur O26 : 14 lignes ≥ 2 mots mal couvertes (IoU < 0,8), 4 sans appariement, aucune avec une candidate ≥ 0,5 → même diagnostic que le dev : les lignes manquantes (texte vertical, lignes serrées) ne sont pas dans les candidates.
- Texte : **852691769/512 : page parfaite** (0 édition, VT distribuée et adjugée, 53/53 lignes, page en tableau). buchdiss : VT fautive corrigée par l'adjudication (24 car.) ; restent le blanc après « „ » (5), une ligne indécise (« cumulaho »), une ligne en trop « )()( », ſ/s.
- Post hoc (hors H-O26, ne compte pas) : R6 (L44, guillemet ouvrant collé, convention OCR-D et VT 36/0) corrigerait les 5 lignes en échec de buchdiss et 5 éditions ; R6 ne touche aucune ligne du dev. À valider sur le prochain jeu neuf (O27) avant adoption.
- Annexe : lectures sans zoom conservées (6) pour mesurer plus tard l'apport des zooms.
