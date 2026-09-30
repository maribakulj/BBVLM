# M01 — métadonnées bibliographiques depuis la page de titre (VLM) contre les notices MODS SBB

Figé le 2026-09-30 (12h47 Paris), avant toute lecture.
Tirage : les 66 œuvres SBB présentes dans les dossiers de travail, ordonnées par sha256("M01"+PPN), 12 premières : ferrepit, aepidisp, dalarie, AmmoLIBR, curineux, 730277879/82603893X, herrleyc, brochrnx, DasWeL, betrdrzwt, chiamerk, buchdas.
Entrée : image de la page de titre (page marquée title_page dans le METS ; sinon 3ᵉ page physique, signalé) ; VT : MODS du même METS (outils/meta_sbb.py, point OAI).
Lecture : 1 passe Opus, consigne figée outils/consigne_M01.md : transcrire la page de titre, puis donner pour chaque champ la forme lue et la forme normalisée « catalogue » (auteur : nom de famille ; lieu : nom moderne allemand ; imprimeur : nom de famille ; année : chiffres arabes) ou « absent de la page ».
Mesure par champ (auteur, lieu, imprimeur, année, titre), par œuvre : juste / faux / absent-à-tort (le champ figure sur la page mais n'est pas donné) / absent-légitime (vérifié à l'image, noté séparément).
- auteur : nom de famille normalisé (minuscules, sans diacritiques, ſ→s, u/v, i/j) égal à celui d'un auteur MODS ;
- année : égale (MODS « 1529 » ; intervalle MODS « [ca. 1700] » : année dans ±5) ;
- lieu : premier mot égal à celui d'un lieu MODS après normalisation (minuscules, sans diacritiques, ck→k, ß→ss ; le catalogue lui-même n'est pas toujours normalisé : « Franckfurt » pour betrdrzwt) ;
- imprimeur : nom de famille présent dans une forme MODS ;
- titre : les 5 premiers mots normalisés du titre MODS (hors « … ») présents dans l'ordre dans la transcription.
Pire cas rapporté : œuvre au plus grand nombre de faux. Pas de moyenne seule : tableau œuvre × champ.
Hypothèse : ≥ 90 % des champs présents sur la page sont justes ; aucun faux sur l'année.
