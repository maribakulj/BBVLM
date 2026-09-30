# M05 — validation sur 12 œuvres neuves (pré-enregistré 30/09 19h45)

Motivation : M03 (identité GND pour le lieu, radicaux latins) et la règle « imprimeur par identité GND » (suggérée par M04b : Egenolphus / Egenolff, Viridimontanus / Rhau-Grunenberg) ont été conçues en voyant les œuvres M01 ; il faut les valider sur des œuvres jamais utilisées pour les métadonnées.
Œuvres : parmi les 43 œuvres du corpus absentes des jeux M01/M01b/M01c, une sur trois dans l'ordre alphabétique (indices 0, 3, …, 33) : 12 œuvres.
Lecture : 1 passe Opus, consigne M01 (outils/consigne_M01.md), page de titre (METS) + page(s) de colophon (bloc METS « colophon », sinon 3 dernières pages de texte hors plats/gardes/mire) ; champ « source » : titre ou colophon.
Mesure : M03 (outils/meta_m03.py) + imprimeur juste si la forme lue appartient (radicaux latins) aux formes GND (lobid, type Person : nom préféré + variantes) d'un imprimeur du MODS.
Hypothèse : ≥ 90 % des champs présents justes (auteur, année, lieu, imprimeur, titre), 0 année fausse.
