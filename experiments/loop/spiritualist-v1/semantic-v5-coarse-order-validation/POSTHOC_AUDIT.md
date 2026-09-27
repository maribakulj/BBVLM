# Audit post-score A09 — page 0050

Le protocole a été figé avant lecture. Une seule passe Luna brute et valide
retrouve 9/9 régions du flux et 3/3 fragments de manchette. Le nouvel
ordonnanceur découvre trois colonnes et reproduit 36/36 relations.

Le gate échoue sur les SSU : F1 de paires 0,733 (précision 0,579, rappel 1,000),
quatre unités prédites contre cinq. Le seul désaccord physique est F3 : le bloc
`tr_1743005255`, hauteur 238 px, est un grand titre multi-ligne que le seuil
0,020 classe TEXT. Il fusionne deux unités successives. Le prochain classifieur
doit exploiter la typographie interne (lignes, taille relative, centrage/densité),
pas relever le seuil sur cette page consommée.

Les genres restent non scorés. 0050 est la dernière page du split initial et
ne sera plus utilisée comme validation indépendante.
