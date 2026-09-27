# A15 — contrôle visuel de l'alignement, 27/09/2026

Les trois fichiers `word-overlay-1.jpg` à `word-overlay-3.jpg` ont été vus par
l'agent principal à résolution native. Rectangles mot superposés au scan,
sans déplacer les pixels de texte.

Défaut manifeste : en fin de première et troisième région, la boîte du token
`:—` entoure surtout les deux-points et laisse dépasser le tiret long. Le texte
est dans l'ALTO mais sa géométrie est incomplète. D'autres fins de mot sont très
serrées ; pas de comptage fiable sans adjudication indépendante.

Les 184 rectangles ont des dimensions positives. Les 20 lignes et leurs textes
sont conservés, cache vérifié, aucun repli natif à confiance zéro. Ce signal ne
valide ni les limites d'encre ni la tokenisation (par exemple `ALPHABET.—A`).
Les vingt lignes gardent le statut automatique et leur demande de relecture.

Ne pas élargir puis déclarer victoire sur cet échantillon consommé. Prochaine
hypothèse : protéger ponctuation, hampes et jambages avec contrôle d'encre
conservateur, garder PERO natif comme baseline et s'abstenir lorsque les
caractères voisins sont ambigus. Puis geler une validation diverse nouvelle.
Aucune GT source n'est corrigée par cet audit non indépendant.

Échecs rencontrés et corrigés : absence d'IDs de lignes dans l'export natif,
puis numpy.bool_ non sérialisable dans le rapport. La liaison des IDs contrôle
texte, comptes et géométrie ; conversion bool explicite. Les reprises ont
réutilisé les logits, sans nouvelle reconnaissance et sans passe VLM.
