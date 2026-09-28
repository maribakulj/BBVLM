# A55b — garde d'expansion horizontale (développement)

Le diagnostic A55 montre que la hauteur est améliorée globalement par A37,
mais que l'IoU horizontal français baisse de 0,8245 à 0,8077. L'implémentation
PERO 0.7.0 construit les mots à partir de l'alignement CTC et d'une extension
fixe dans la géométrie du crop de ligne ; notre raffinement A32 remplace cette
étendue par toute l'encre de la cellule délimitée aux milieux entre mots. A37
ne garde que la hauteur : il autorise donc une expansion horizontale nuisible.

## Ablation pré-déclarée

Sur A54 consommé uniquement, tester les plafonds d'expansion de largeur
`1.00, 1.02, 1.05, 1.10, 1.20` appliqués après la règle A37. Une boîte raffinée
est acceptée si sa hauteur n'excède pas la native et si sa largeur n'excède pas
`plafond × largeur_native`; sinon la boîte native est conservée.

Sélectionner le plafond de meilleur IoU moyen global sous les deux contraintes :

1. IoU moyen français au moins égal au natif ;
2. aucune baisse de plus de 0,01 d'IoU moyen sur un bloc français.

Cette sélection est un réglage de développement. Elle ne vaut pas validation,
ne modifie aucune référence et devra être exécutée à l'aveugle sur un nouveau
lot gelé avant promotion.

