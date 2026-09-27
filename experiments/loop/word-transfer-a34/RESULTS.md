# A34 — transfert indépendant des boîtes de mots

## Décision

Conserver **A32**, rejeter **A34**. Le raffinement corps+satellites A32 se
transfère nettement mieux que les boîtes PERO natives sur ces douze pages, mais
il reste très loin de boîtes parfaites. La règle A34 « ponctuation terminale,
aire ≥20 px, sauf `*` » échoue à son gate local : un gain et six régressions.

Cette expérience est une validation de transfert géométrique sur trois ouvrages
historiques allemands/latins, pas une validation de presse française. Elle
utilise en outre les lignes, le texte et l'ordre des tokens de référence.

## Mesures

12 pages, 515 lignes et 4 759 mots de référence :

| Méthode | Mots prédits | IoU moyen | Rappel IoU≥0,5 | Rappel IoU≥0,8 |
|---|---:|---:|---:|---:|
| PERO natif | 4 768 | 0,654863 | 81,34 % | 19,04 % |
| CTC forcé | 4 759 | 0,660059 | 82,96 % | 20,24 % |
| Cellule + Otsu brut | 4 759 | 0,787304 | 94,01 % | 52,47 % |
| A32 corps+satellites | 4 759 | **0,812303** | **95,63 %** | **58,94 %** |
| A34 ponctuation conservatrice | 4 759 | 0,812216 | 95,57 % | 58,94 % |

A32 bat PERO natif dans chacun des trois ouvrages. Ce résultat n'est cependant
pas end-to-end : la segmentation en lignes, le texte et la cardinalité/ordre
des mots sont oracle. Les baselines synthétiques peuvent aussi désavantager les
boîtes natives PERO.

Le CER PERO natif sur ce corpus est 13,97 % strict et 5,51 % après la
décomposition de glyphes déjà documentée. Il ne mesure ni l'OCR VLM français
ni l'objectif opérationnel Gallica/Exalead.

## Audit exhaustif des sept changements A34

L'image `all-changes-clean.png` montre uniquement les pixels originaux. Le seul
gain est `Laquayen,` (IoU 0,575→0,642). Les six pertes sont `vornemen:`, `7.`,
`geben.`, `werden,` et deux occurrences de `Hrn.` : la composante ajoutée
appartient visuellement à l'encre voisine ou inférieure. Le texte indique qu'un
signe final est attendu, mais ne localise pas ce signe. Un seuil d'aire ne
résout donc pas l'ambiguïté topologique.

## Coût et intégrité

Chargement modèle 0,063 s, 515 forwards CPU en 10,874 s, alignement 5,407 s,
deux raffinements de composantes en 8,828 s, 26,588 s au total, zéro passe VLM.
Les blobs source et les entrées protégées sont vérifiés et aucune GT n'est
remplacée.

Deux défauts d'adaptateur ont été corrigés après ouverture mais avant tout
rapport/score : copie redondante d'une empreinte de protocole et représentation
explicite d'une ligne OCR vide. La règle candidate était gelée avant ouverture,
mais l'évaluateur complet ne peut pas être qualifié de gel procédural parfait.
Le détail est dans `AMENDMENT.md`; aucun gate projet n'est accordé.

## Suite décidée

Ne plus régler une heuristique « signe annoncé ⇒ composante la plus proche »
sur ces données désormais consommées. La prochaine hypothèse géométrique doit
exploiter l'étendue temporelle CTC/caractère ou une confiance de rattachement,
puis être gelée avant un nouvel ensemble indépendant. Il faut parallèlement
obtenir une vraie GT française au mot ou une adjudication indépendante : un
corpus qui annonce des « mots » textuels sans nœuds géométriques `Word` ne
suffit pas.
