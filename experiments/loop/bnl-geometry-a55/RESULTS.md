# A55 — résultat : le défaut est mixte et la garde de largeur échoue

## Diagnostic des 1 957 mots appariés

| périmètre | variante | IoU moyen | IoU80 | IoU horizontal | IoU vertical | ratio hauteur médian |
|---|---:|---:|---:|---:|---:|---:|
| tous | PERO natif | 0,5807 | 2,50 % | 0,8299 | 0,6775 | 1,456 |
| tous | A37 | **0,6685** | **33,57 %** | **0,8426** | **0,7562** | **1,202** |
| français | PERO natif | 0,5763 | 5,91 % | **0,8245** | **0,6781** | 1,443 |
| français | A37 | **0,5844** | **15,71 %** | 0,8077 | 0,6753 | **1,309** |

A37 reste positif globalement, mais son gain français masque des blocs opposés :
`0645` monte de 0,699 à 0,832 et `0345` de 0,609 à 0,728, tandis que `0887`
baisse de 0,551 à 0,481, `0164` de 0,547 à 0,486 et `0456` de 0,649 à 0,572.
Les quatre bords sont rarement à moins de 10 % d'une hauteur de référence ; ce
n'est donc pas un simple décalage vertical uniforme.

## A55b — résultat négatif

Les cinq plafonds d'expansion horizontale `1,00–1,20` augmentent progressivement
l'IoU global de 0,6063 à 0,6563, sans atteindre A37 (0,6685). Aucun ne satisfait
la règle pré-déclarée de non-régression par bloc français. Le meilleur plafond
pour la moyenne française (`1,20`, IoU 0,5806) laisse `0164` à 0,486 et `0887`
à 0,481. La boîte affinée peut être plus étroite que la boîte CTC tout en étant
attachée à la mauvaise étendue d'encre ; une limite de largeur ne suffit pas.

## Interprétation

- Rejet de la garde globale de largeur : aucune modification de production.
- Les rectangles BnL au mot ne sont pas une vérité parfaite documentée. Ils
  restent utiles pour exposer des régimes, pas pour déclarer des boîtes ALTO
  exactes ni régler un routeur jusqu'à 100 %.
- La visualisation confirme que les sorties natives PERO sont des enveloppes
  dérivées du crop de ligne/alignement CTC, alors que le raffinement suit
  l'encre. Les deux conventions ne coïncident pas toujours avec les rectangles
  du fournisseur.
- Prochaine expérience : chercher/fixer un corpus dont les polygones de mots
  sont explicitement manuels ou doublement contrôlés. En parallèle, un garde
  de propriété locale devra raisonner sur la ligne et la composante, pas sur la
  seule largeur du rectangle.

A55 est un diagnostic sur données consommées. Il ne ferme aucun des sept
critères globaux.

