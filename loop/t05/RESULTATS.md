# T05 — mots soudés à la lecture détectés par les blancs d'encre intra-mot (L40) — NÉGATIF (essai, 30/09 20h05)

Sonde (outils/soudure.py) : alignement forcé CTC (W05) de la ligne lue, espaces compris ; largeur du blanc d'encre (colonnes vides dans la bande centrale de la ligne) à chaque frontière de caractère ; comparaison des blancs intra-mot aux blancs inter-mots de la même ligne.
Essai sur les soudures connues (audit A04) :
| ligne | blancs inter-mots (px) | plus grands blancs intra-mot | soudure cherchée |
|---|---|---|---|
| hackherz « ihmviel beſſer/ … » | 1, 2, 5, 7, 8, 12, 17 | 5 (weh|let, ſon|der…) | « ihm|viel » absent des plus grands |
| hackherz « Glaͤubigetragen/ … » | 0, 0, 0, 2, 3, 3, 6, 11 | 7, 7, 4, 3 | non isolée |
| AphoqvSuS « VerboDEI, quod … » | 0, 3, 11, 11 | 18 (erreur d'alignement « m T »), 5, 4 | « rbo|DEI » = 4 px |
| baltdiss « traher e … » | 8 à 18 | 7 | — |
Les deux distributions se recouvrent entièrement dans ces compositions serrées (blancs inter-mots de 0 à 2 px fréquents) : pas de seuil possible. Piste close (comme T02, perte CTC comme arbitre des blancs).
