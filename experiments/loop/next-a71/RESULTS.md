# A71 — audit visuel aveugle des absences A70

## Résultat

Un lecteur primaire Luna a inspecté 12 vues opaques, sélectionnées de façon
déterministe parmi les 63 lignes A70 auxquelles aucune boîte détectée ne
contribue au moins 1 %. Les identifiants et les SHA-256 ont été vérifiés avant
agrégation.

- 11/12 vues contiennent du texte visiblement imprimé ; 1/12 reste ambiguë.
- 5/12 seulement autorisent, selon le lecteur, une récupération rectangulaire
  sans inclure manifestement des lignes voisines ou des ornements.
- 0/12 a été classée comme simple règle ou non-texte.
- Aucun texte de référence, aucune page Test et aucune nouvelle vérité terrain
  n'ont été ouverts ou modifiés.

Le diagnostic A70 correspond donc principalement à de vrais manques de rappel
sur de l'encre textuelle, et non à une pure divergence de convention. En
revanche, élargir naïvement les rectangles serait dangereux dans 7/12 cas :
plusieurs vues coupent des lignes adjacentes, des titres ornementaux ou du texte
aux bords. Une segmentation pixelwise/ligne est désormais un candidat motivé ;
la fusion ou le padding rectangulaire global restent rejetés.

## Portée et limites

Cette sélection est oracle et issue des pages A69 déjà consommées. Un seul
lecteur visuel n'est ni une adjudication ni une vérité terrain de boîtes. La
présence de texte ne définit pas l'appartenance à un article, l'ordre de lecture
ou une boîte ALTO parfaite. A71 ne produit aucun CER et ne valide aucun des sept
critères globaux.

## Décision suivante

A72 doit comparer de manière bornée le rappel de lignes d'une segmentation
pixelwise Eynollah (ou une ablation équivalente) aux prédictions YOLO scellées,
sur données consommées et sans OCR complet. Avant toute installation lourde,
consigner précisément dépendances, poids, coût et sous-étages exécutés. La
validation diverse restera à figer après le développement.

