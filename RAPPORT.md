# BBVLM — rapport

Produire de l'ALTO **au mot** de qualité vérité terrain, à partir d'un texte lu par
un VLM de frontière. Ce rapport dit ce qui est établi, ce qui est réfuté, ce que
ça coûte, et où sont les limites de chaque chiffre.

Toutes les mesures portent leur périmètre. Aucune n'est une moyenne entre corpus :
`CRITERE.md`, gelé le 25/09 avant toute mesure de candidat, exige que chaque seuil
soit tenu **sur chaque corpus**.

---

## 1. Ce qui est établi

### L'architecture en trois étages

| étage | rôle | coût | ce qu'il vaut |
|---|---|---|---|
| `connexe` | place toutes les boîtes | 119 ms/ligne | 99,35 % et 99,12 % des frontières sous 0,5 caractère sur BnF et PetitParisien |
| comité de 5 moteurs | désigne les douteuses | 5× le moteur | AUC 0,824 ; 56 % des mauvaises boîtes dans 20 % des mots |
| VLM sur règle graduée | remesure celles-là | ~0,5 planche par mot | 96,6 % contre 86,2 % sur le décile désigné |

L'étage 3 n'existe que grâce à l'étage 2. Mesuré séparément (B60, 61 mots, tirage
équilibré), le relevé du VLM **ne bat pas** le moteur : égalité parfaite sur le
critère gelé, et tête-à-tête perdu 18 contre 26 sur la métrique stricte. Mesuré
sur le décile que le comité désigne (B61, 35 mots), il le bat nettement. Les deux
résultats sont cohérents et c'est leur conjonction qui fonde la cascade.

### Le moteur géométrique, mesuré sur le corpus complet (B49)

8246 lignes, 45 195 frontières, sans troncature.

| corpus | ≤0,5c ≥95 % | pire ≤3c | IoU ≥0,80 | vs proportionnel |
|---|---|---|---|---|
| BnF (1 page, 538 l.) | 99,35 ✓ | 1,84 ✓ | 0,945 ✓ | 1,84 / 3,38 ✓ |
| PetitParisien (1 page, 104 l.) | 99,12 ✓ | 1,32 ✓ | 0,897 ✓ | 1,32 / 2,14 ✓ |
| Newseye (9 pages, 7586 l.) | 94,77 ✗ | 33,31 ✗ | 0,867 ✓ | 33,31 / 28,60 ✗ |
| BNLfull (1 page, 18 l.) | 34,43 ✗ | 8,99 ✗ | 0,000 ✗ | 8,99 / 2,79 ✗ |

**Neuf seuils tenus sur seize, deux corpus conformes sur quatre.**

Sur Newseye, la clause de non-régression tombe sur **une frontière sur 45 195** :
`connexe` y domine le proportionnel à tous les quantiles (médiane 0,00 contre
0,94 ; p90 1,44 contre 3,08 ; p99 7,90 contre 10,26 ; 464 frontières au-dessus de
3 caractères contre 991) et n'est pire que sur le maximum absolu. Le critère
reste gelé — on ne rature pas un critère parce qu'on le rate — mais le fait doit
être lu avec sa distribution.

### La cause de la queue extrême (B52, B53)

Le pire cas de Newseye, regardé et non supposé : une boîte de ligne de la vérité
terrain qui **franchit le filet de colonne**. L'encre du mot voisin entre dans le
support, le moteur y étire son gabarit, et place un mot dans l'autre colonne.

```
boîte de ligne VT : 2541 -> 3364        (le filet est vers 3340)
boîtes VT         : ouvrier 2542-2671 | . 2692-2698
boîtes connexe    : ouvrier 2542-3330 | . 3353-3363
```

Prévalence : 0,9 % des lignes de Newseye, **0 % de BnF et de PetitParisien**.
Rare, mais c'est de là que vient toute la queue.

### Les deux instruments du VLM, et leurs domaines

| instrument | ce qu'il voit | ce qu'il ne voit pas | coût |
|---|---|---|---|
| relevé sur règle graduée | la position d'une frontière à 0,2 car près | — | 0,5 planche par mot |
| dépistage visuel par ligne | les fautes **catégorielles** — précision 100 %, rappel 67 % au-dessus de 1 car | l'imprécision métrique — rappel 22 % à 0,5 car | 1 regard par ligne |

Le dépistage a vu une boîte posée sur le filet de colonne et un mot de la colonne
voisine : exactement le défaut que les statistiques internes du moteur ne savent
pas trouver.

---

## 2. Ce qui est réfuté

| piste | résultat | cause |
|---|---|---|
| **B41** — prédire les échecs du moteur par ses propres indices | AUC 0,663 ; router 20 % ne rattrape que 42 % | Les sept indices décrivaient la géométrie locale de l'encre, celle dont `connexe` se sert pour décider. Un indice calculé sur la décision ne peut pas en être indépendant. B43 l'a confirmé en réussissant depuis l'extérieur. |
| **B40** — le VLM bat le moteur sur règle | Infirmé par B60 | L'échantillon de B40 (6 mots) était stratifié sur l'erreur de `connexe`, un tiers au-dessus de 0,5 caractère : cela revenait à comparer un relevé neuf aux pires cas de son adversaire. |
| **B52** — le mauvais aiguillage vers le moteur de tableau coûte cher | Il ne coûte rien | La règle « 70 % de mots de trois caractères ou moins » attrape bien de la prose française (les mots outils sont courts), mais sur les 90 lignes concernées le moteur reçu à tort fait *légèrement mieux*. Non corrigé, délibérément. |
| **B55** — détecter l'encre étrangère par un seuil | Aucun seuil ne sépare | Au mieux 11 lignes polluées sur 70 attrapées pour 16 lignes saines abîmées. |
| **B57** — rogner le support sur un seuil de largeur | Effondrement sur BNL (pire cas 8,99 → 17,75) | Dans un tableau, un blanc large est une structure de colonne, pas de la pollution. |
| **B58** — rogner en laissant le DTW arbitrer, avec garde tabulaire | Échange, non promu | Pire cas −2,53 caractères, frontières −0,42 point. `CRITERE.md` place les frontières en premier. |
| **B36** — un gabarit Fraktur améliore la géométrie sur du Fraktur | Écarté | Le coût DTW mesure la ressemblance de deux profils, pas la justesse des frontières : le gabarit Fraktur fait passer les chevauchements de 10 à 16. |

---

## 3. Limites

**Les chiffres du champion antérieurs à B49 étaient faux.** Ils avaient été
obtenus avec `BBVLM_MAX_LIGNES`, qui tronque à quelques dizaines de lignes par
page. Sur BnF, 20 lignes donnent 100 % et IoU 0,939 — exactement le chiffre
enregistré — quand les 538 lignes réelles donnent 99,35 % et un pire cas de 1,84.
`run.py` imprime et enregistre désormais le périmètre de chaque mesure.

**Le corpus contenait un doublon.** `BNL` est entièrement inclus dans `BNLfull` :
37 pages comptaient double, et leurs mesures identiques avaient l'air de deux
confirmations indépendantes. `all_pages()` déduplique par contenu.

**Le décile disputé n'est pas ce qu'on croyait.** Il est en grande partie composé
de lignes tabulaires et de lignes dont le **texte** de la vérité terrain est
dégradé (`6équenee3`, `<o`, `»*`, `'8tl*`). Le comité détecte donc aussi la
mauvaise qualité du texte, pas seulement la difficulté géométrique. C'est utile,
mais ce n'est pas la grandeur qu'on pensait mesurer.

**Les effectifs.** B61 porte sur 35 mots et 6 lignes ; B60 sur 61 mots ; B44 sur
57 boîtes dont 3 au-dessus d'un caractère. Ce sont des indices, pas des mesures
établies. Le moteur, lui, est mesuré sur 45 195 frontières.

**Le pire cas du relevé du VLM est plus mauvais que celui du moteur** (3,46 contre
1,03 sur la métrique gelée). Il vient des lignes dont le jeton de vérité terrain
est illisible et où le placement était une conjecture — défaut de vérité terrain
plutôt que de lecture, mais il compte dans le chiffre.

**Vérification due et non faite** : le multi-gabarit de `dtw.py`
(`BBVLM_FONTES=toutes`) n'a jamais été mesuré sans régression sur un échantillon
réduit ; il est désarmé par défaut.

---

## 4. Ce que ça coûte

Pour une page de 100 lignes et 700 mots :

| étage | volume | coût |
|---|---|---|
| `connexe` | 100 lignes | 12 s |
| comité de 5 moteurs | 100 lignes | ~60 s |
| relevé sur règle | 70 mots (le décile) | ~35 planches à regarder |

Le troisième étage est le seul qui demande un VLM de frontière, et il ne
s'applique qu'à un mot sur dix.

---

## 5. Les artefacts

Deux ALTO au mot produits par la chaîne complète, texte lu par le VLM **à
l'aveugle** sans accès à la vérité terrain. Les deux sont dans le dépôt avec leur
overlay et leur provenance.

### `out-pp/` — Le Petit Parisien, 15 lignes, là où le moteur tient

```
lecture    : 14 lignes sur 15 identiques à la VT, CER 0,16 %
géométrie  : 15 TextLine, 115 String, 0 chevauchement, 0 dimension nulle
doute      : 12 mots marqués a_remesurer (10,4 %)
```

L'overlay montre chaque boîte collant son mot sur les quinze lignes.

### `out-finale/` — BNL 0015, page complète de 18 lignes, là où le moteur échoue

```
lecture    : 16 lignes sur 18 identiques à la VT
             — un écart est un choix d'encodage (guillemet de répétition)
             — l'autre est une ERREUR DE LA VT : elle écrit « Esch-sur-I'Alzette »
               avec un I majuscule là où le texte porte l'article « l' »
géométrie  : 18 TextLine, 79 String, 4 chevauchements
doute      : 7 mots marqués a_remesurer (8,9 %)
```

**L'overlay de cette page est mauvais** : les boîtes débordent d'une ligne sur
l'autre et se chevauchent. C'est exactement ce que le banc annonçait — 34,43 %
des frontières sous 0,5 caractère, IoU médian 0,000 sur ce corpus. L'artefact est
conservé tel quel : un rapport qui ne montrerait que le cas favorable ne dirait
rien d'utile.

**Ce que les deux artefacts établissent ensemble** : sur un tableau financier à
colonnes, la lecture du VLM reste juste (16/18 lignes, et elle corrige même la
vérité terrain) tandis que la géométrie s'effondre. Le verrou n'est pas le texte.

### Ce que ces ALTO ne sont pas

Les mots marqués `a_remesurer` n'ont **pas** été vérifiés au relevé sur règle. Ces
fichiers sont des productions, pas des vérités terrain certifiées. Une VT exige
que le troisième étage tourne sur les mots marqués, ce qui demande un regard
humain ou un VLM par mot — c'est le coût annoncé en section 4.
