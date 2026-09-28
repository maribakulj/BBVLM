# A78 — regroupement horizontal borné, développement consommé

Hypothèse gelée avant calcul, 28 septembre 2026 : le défaut visuel A77 des mots
espacés peut être réduit par liens horizontaux entre composantes proches en y.
Ce test porte exclusivement sur les 4 pages A76 consommées, sans prétention
indépendante. Aucune nouvelle inférence, aucun texte et aucun XML en prédiction.

Une seule configuration : boîtes disjointes en x, gap <=1,5 fois la plus petite
hauteur, recouvrement vertical >=70 % de la plus petite hauteur, ratio des
hauteurs <=1,5, différence des centres y <=25 % de la plus petite hauteur.
Ne joindre que les voisins mutuellement les plus proches à droite/gauche parmi
ces paires éligibles ; ties par identifiant de composante. Les groupes transitifs
sont autorisés et explicitement comptés. Aucun filtre des petits candidats.
Le rectangle du groupe est l'union englobante. Chaque composante figure une
seule fois ; aucune perte de surface de boîte initiale.

Sceller toutes les boîtes avant accès aux XML. Réutiliser exactement le score
A75/A76 (Hongrois max-somme IoU, seuils 0,5/0,7) et ses limites. Rapporter chaque
page, paires de référence qui perdent/gagnent le seuil IoU50, et nombre de groupes.
Décision locale : précision ET rappel IoU50 non inférieurs sur chaque page,
au moins une vraie correspondance supplémentaire au total. Rejeter si un seul
critère échoue ; ne pas régler de seuil sur ce résultat. Même réussite => nouveau
jeu indépendant requis, aucune promotion globale. Les 100 Test restent intacts.
