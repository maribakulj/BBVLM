# Consigne I01 — signe d'inflexion de l'imprimeur (même appel que l'arbitre P3)

Entrée : DOSSIER/inflexion/taches.json — {id, image, ligne, mots}. Chaque image
est une ligne recadrée et agrandie ; « mots » liste les mots qui portent un
signe au-dessus d'un u, écrit « u* ».
Pour chaque mot, regarde de très près le signe et classe sa FORME (jamais la
langue) : "anneau" (petit rond fermé ou presque), "e" (petit e : boucle ouverte
avec trait, crochet, deux traits accolés), "points" (deux points nets
séparés), "absent" (mot invisible ou illisible sur l'image).
Sortie : DOSSIER/inflexion/verdicts.json — liste de {"id", "signes": [un par
mot, dans l'ordre], "remarque"}. Aucun autre fichier.
