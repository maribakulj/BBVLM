# M05 — validation sur 12 œuvres neuves (jamais utilisées pour les métadonnées) — HYPOTHÈSE TENUE

1 passe Opus par œuvre (consigne M01), page de titre + colophon (bloc METS « colophon » : branchri, culmsent ; sinon 3 dernières pages de texte) ; mesure M03 + auteur et imprimeur par identité GND (lobid, type Person, formes cherchées d'après le nom MODS ; M02 passait par le lien K10plus : écart de mise en œuvre).

| | justes | faux | absents | sans VT |
|---|---|---|---|---|
| 12 œuvres, 5 champs | **43** | 2 | 7 | 8 |
Champs présents justes : **43/45 = 95,6 %** (seuil 90 %) ; **0 année fausse**. Détail : m01/mesure_M05.txt.

- Colophon utile : culmsent (Nürnberg, Petreius, 1540 : les trois champs viennent du colophon), branchri (lieu et imprimeur) ; les autres œuvres (XVIIe-XVIIIe s.) portent l'adresse sur la page de titre.
- Faux : emmeprac auteur (« Ioanne Emerico à Rosbach » normalisé « Rosbach », nom de lieu, au lieu d'« Emmerich » : erreur d'interprétation) ; catapabin titre (la page de titre fournie par le METS est la page française d'un catalogue bilingue ; le MODS donne le titre latin : lecture fidèle, page non conforme à la référence).
- Absents : années non imprimées (branchri, durrgeda : seule la date du décès), lieux d'impression non imprimés (baurodwe), catapabin (lieu de vente, pas d'impression : exclu à bon droit par le lecteur).
Conclusion : la chaîne métadonnées (page de titre + colophon choisi par la structure METS, mesure par identité) tient sur des œuvres neuves au niveau observé en développement (M03 97,4 %).
