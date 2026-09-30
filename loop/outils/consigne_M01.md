# Consigne M01 — métadonnées d'une page de titre d'imprimé ancien

Tu reçois l'image d'une page (normalement la page de titre) d'un imprimé ancien (XVIᵉ-XIXᵉ s., allemand ou latin, Fraktur ou antiqua).

1. Transcris d'abord intégralement le texte imprimé de la page, ligne par ligne, tel qu'imprimé (ſ, u/v, abréviations comme imprimées ; pas de modernisation).
2. Puis, pour chacun des champs ci-dessous, donne :
   - `lu` : la forme exacte telle qu'elle apparaît sur la page (ou null) ;
   - `norme` : la forme « catalogue » normalisée, ou null si le champ n'est pas sur la page.
   Champs :
   - `auteur` : l'auteur (pas un dédicataire, pas le praeses ou le respondant sauf s'il est l'auteur désigné) ; `norme` = nom de famille seul, en forme allemande usuelle si le nom est latinisé et que la forme vernaculaire est évidente, sinon tel quel.
   - `titre` : les premiers mots du titre ; `norme` = mêmes mots, orthographe de la page mais ſ→s.
   - `lieu` : lieu d'impression ; `norme` = nom moderne allemand du lieu (ex. « Hagenaw » → « Hagenau », « Lipsiae » → « Leipzig », « Francofurti ad Moenum » → « Frankfurt, Main »).
   - `imprimeur` : imprimeur ou éditeur/libraire ; `norme` = nom de famille seul.
   - `annee` : année d'impression ; `norme` = année en chiffres arabes (convertis les chiffres romains ; « M.D.XXIX » → 1529).
3. N'invente rien : si un champ n'est pas imprimé sur cette page, `lu` et `norme` valent null. Ne complète pas par ta connaissance de l'œuvre.

Sortie : un fichier JSON {"transcription": "...", "champs": {"auteur": {"lu": ..., "norme": ...}, "titre": {...}, "lieu": {...}, "imprimeur": {...}, "annee": {...}}, "page_de_titre": true|false}.
