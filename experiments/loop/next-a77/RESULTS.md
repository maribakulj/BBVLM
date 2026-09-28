# A77 — attribution mesurée, sans nouvelle inférence

Sur les quatre pages A76 déjà consommées, le compteur ancien « plusieurs
références avec IoU de rectangle >0,1 » vaut **841**, contre **197** composantes
ayant plusieurs contacts substantiels selon les pixels des polygones. Les
critères ne sont pas équivalents : ni 841 ni 197 ne sont des fusions visuellement
certifiées. Le premier nom était trop affirmatif ; les fichiers anciens restent
intacts, leur interprétation est corrigée ici.

| Page | Ancien contact rectangle multiple | Contact pixel multiple | Références touchées par plusieurs composantes >=5 % | Pixels prédits dans plusieurs références |
|---|---:|---:|---:|---:|
| 1626 |32|0|0|1,52 %|
| 1785 |28|2|2|0,48 %|
| 1866 |537|68|415|9,24 %|
| 1924 |244|127|237|14,69 %|

Aucune ligne de référence n'a zéro pixel prédit. Cela ne signifie pas que toute
la ligne soit couverte ou lisible. Le chevauchement des annotations rend
également les comptes de fragments ambigus, surtout sur les pages récentes.

## Inspection réelle

L'agent principal a inspecté witness-0-raw, witness-0-overlay et witness-3-overlay.
Dans witness-0, une ligne à grands espaces entre mots est réellement découpée
horizontalement en plusieurs boîtes. Dans witness-3, la grande boîte de la ligne
centrale reste distincte des deux fragments de la ligne supérieure ; compter les
contacts avec plusieurs références comme des fusions serait trompeur.
Ce n'est ni une adjudication indépendante ni une passe OCR.

## Regroupement oracle : diagnostic, jamais système candidat

En attribuant chaque composante contenue à >=80 % à sa référence dominante,
puis en englobant celles de la même ligne, la précision/rappel IoU50 vaut
100/100 % (1626), 100/93,41 % (1785), 100/80,62 % (1866), 98,82/76,83 % (1924).
Même cette politique dépendante des références abandonne trop de lignes : un
regroupement horizontal seul ne résout pas toute l'ambiguïté. Ce n'est pas un
plafond mathématique pour tous les systèmes possibles, mais un oracle restreint.

## Coût et décision

0,87 s CPU pour diagnostic et six paires de vues ; zéro inférence nouvelle,
OCR, VLM ou Test. Entrées et XML inchangés (hashes avant/après), 1 306 candidats
et 1 103 références réconciliés aux comptes A76. Aucun gate promu.
A78 peut mesurer un regroupement horizontal image-only borné, développé sur
ces pages consommées, en pénalisant explicitement les fusions. Il faudra un
nouveau gel avant toute validation. Ne pas réutiliser A76 comme indépendant.
