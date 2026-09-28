# A55 — diagnostic gelé des erreurs de bords

## Objet

Décomposer, sans retoucher les paramètres, l'écart géométrique observé sur les
16 blocs BnL A54 déjà consommés. A55 n'est donc pas une validation indépendante
et ne peut promouvoir aucun candidat.

## Entrées scellées

- références BnL A54 originales, coordonnées `mm10` converties à 300 ppp ;
- sorties PERO natives A54 ;
- sorties A37 routées A54 ;
- langue déjà consignée par l'audit A54.

## Appariement et métriques pré-déclarés

1. apparier les lignes par assignation hongroise sur l'IoU ;
2. dans chaque paire de lignes, apparier les mots dans leur ordre horizontal
   quand les cardinalités concordent, sinon par assignation hongroise sur le
   maximum de l'IoU horizontal natif/routé ;
3. publier séparément IoU horizontal et vertical, erreurs signées des quatre
   bords normalisées par la hauteur de la boîte de référence, rapports
   largeur/hauteur, et taux de bords à 10 % près ;
4. publier tous les blocs et le sous-ensemble français ;
5. conserver les correspondances brutes dans le rapport.

## Décision

- erreur surtout verticale : tester ensuite une estimation locale de la bande
  d'encre, sans déplacer les séparateurs CTC ;
- erreur surtout horizontale : agir sur l'alignement CTC/séparateurs ;
- erreurs mixtes ou références incohérentes : ne pas régler un nouveau modèle
  sur ces boîtes ; chercher une vérité terrain de mots explicitement auditée.

La géométrie BnL au mot reste diagnostique : le fournisseur documente la
double saisie du texte, pas une adjudication manuelle parfaite de chaque boîte.

