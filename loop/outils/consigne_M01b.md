# Consigne M01b (M01 + rôles d'auteur et partie du nom) — métadonnées d'une page de titre d'imprimé ancien

Tu reçois l'image d'une page (normalement la page de titre) d'un imprimé ancien (XVIᵉ-XIXᵉ s., allemand ou latin, Fraktur ou antiqua).

1. Transcris d'abord intégralement le texte imprimé de la page, ligne par ligne, tel qu'imprimé (ſ, u/v, abréviations comme imprimées ; pas de modernisation).
2. Puis, pour chacun des champs ci-dessous, donne :
   - `lu` : la forme exacte telle qu'elle apparaît sur la page (ou null) ;
   - `norme` : la forme « catalogue » normalisée, ou null si le champ n'est pas sur la page.
   Champs :
   - `auteur` : la ou les personnes que la page présente comme responsables de l'œuvre : auteur, et pour une thèse ou disputation le praeses ET le respondant ; pour un livret, des airs ou une pièce mise en musique, le compositeur aussi (le traducteur ou l'éditeur seulement s'il n'y a personne d'autre). Pas un dédicataire. `norme` = liste des noms de famille, séparés par « ; ». Nom de famille : le nom qui suit le ou les prénoms ; si un prénom est suivi d'une initiale puis d'un surnom d'origine (« Ioannes F. Montanus »), l'initiale abrège le nom de famille : écris l'initiale suivie d'un point (« F. ») et ajoute le surnom entre parenthèses. Forme allemande usuelle si le nom est latinisé et que la forme vernaculaire est évidente (« Aepinus » reste « Aepinus »), sinon tel quel.
   - `titre` : les premiers mots du titre ; `norme` = mêmes mots, orthographe de la page mais ſ→s.
   - `lieu` : lieu d'impression ; `norme` = nom moderne allemand du lieu (ex. « Hagenaw » → « Hagenau », « Lipsiae » → « Leipzig », « Francofurti ad Moenum » → « Frankfurt, Main »).
   - `imprimeur` : imprimeur ou éditeur/libraire ; `norme` = nom de famille seul (au nominatif, forme du nom tel qu'il serait cité : « Typis Adleri » → « Adler »).
   - `annee` : année d'impression ; `norme` = année en chiffres arabes (convertis les chiffres romains ; « M.D.XXIX » → 1529).
3. N'invente rien : si un champ n'est pas imprimé sur cette page, `lu` et `norme` valent null. Ne complète pas par ta connaissance de l'œuvre.

Sortie : un fichier JSON {"transcription": "...", "champs": {"auteur": {"lu": ..., "norme": ...}, "titre": {...}, "lieu": {...}, "imprimeur": {...}, "annee": {...}}, "page_de_titre": true|false}.
