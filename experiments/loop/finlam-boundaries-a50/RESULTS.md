# A50 — frontières d’articles sans titre

## Hypothèse mesurée

A49 obtenait déjà 98,80 % d’ordre interne aux articles, mais seulement 66,32 %
de F1 de paires d’article. L’hypothèse « il manque surtout la page adjacente »
est réfutée sur les six pages consommées : seulement 3 des 69 articles sans
zone `TITLE` (4,35 %) existent sur plusieurs pages. Les autres sont surtout des
brèves, annonces, spectacles et publicités composés de blocs `TEXT`.

## Système testé

La géométrie A49 conserve les colonnes et l’ordre physique. Un routeur CPU ne
présente au lecteur que les transitions sans `TITLE` dont l’écart vertical est
supérieur à 0,4 % de la hauteur de page ou le recouvrement horizontal inférieur
à 25 %. Sur la page de stress consommée 186 (260 zones, 40 articles, 23 sans
titre), cela produit 50 frontières sous forme de neuf planches d’images. Luna
voit des identifiants opaques et répond `same_article`, `new_article` ou
`unclear`; il ne voit ni IDs d’article, ni texte de référence, ni score.

## Résultat

- classification de frontière : précision 81,82 %, rappel 78,26 %, F1 80,00 % ;
- regroupement titre-seul : F1 58,69 % ;
- titre + décisions Luna : F1 90,93 % ;
- précision des paires d’article : 42,28 % → 92,33 % ;
- coût : une passe Luna, neuf images, aucune passe VLM de layout ou d’OCR.

Ce résultat justifie une passe VLM ciblée : elle apporte ici la sémantique qui
manque réellement aux boîtes et titres, au lieu de refaire les colonnes. Il ne
ferme aucun gate : la page est consommée, les polygones/classes sont oracle, et
le premier préparateur A50 consultait la présence d’un ID d’article pour omettre
les arêtes non annotées. Cette fuite de routage est supprimée avant A51.

## Audit de convention

Plusieurs « faux positifs » visuels sont éditorialement plausibles : Luna sépare
deux annonces ou deux brèves manifestement distinctes alors que la référence les
regroupe. La mesure quantifie donc l’accord à la convention Finlam, pas une
vérité parfaite universelle. Sorties, erreurs et annotations restent séparées.

## Suite gelée

A51 fixe huit lignes avant ouverture, le même routeur et le même prompt. Les
deux premières pages servent de pilote indépendant ; les six autres restent
réservées tant qu’elles ne sont pas ouvertes. Le gate complet exige F1 article
≥ 0,80, ordre global ≥ 0,90, ordre interne ≥ 0,98, gain contre le titre-seul et
aucune régression de page.
