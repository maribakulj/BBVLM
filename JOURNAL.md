# Journal — boîtes ALTO au mot, from scratch

## Banc

3 corpus, 39 pages, 1151 lignes, **7 689 mots**, choisis pour ne pas se
ressembler :

| corpus | pages | matière | résolution |
|---|---|---|---|
| PetitParisien | 1 col. | presse française 1900, VT vérifiée à la main | 5060×6708 |
| BnF | 1 | presse française, ALTO producteur | 9,6 Mo |
| BNL | 37 | presse luxembourgeoise, **dont du Fraktur** | 796×998 — basse |

## Mesure 0 — lignes de base (2026-09-25)

| boxer | p90 | max | ≤0,5c | IoU méd | PetitParisien | BnF | BNL |
|---|---|---|---|---|---|---|---|
| proportionnel | 0,668c | 3,38c | 85,0 % | 0,585 | 86,7 % | 86,2 % | 83,6 % |
| inkgap DP | 3,539c | 54,9c | 64,7 % | 0,585 | **95,9 %** | **97,2 %** | **28,6 %** ⚠️ |

**Lecture.** Le DP écrase le proportionnel là où l'encre est lisible (95-97 %)
et s'effondre sur BNL (28,6 %, pire cas 54,9 caractères, IoU 0,207). BNL est
le corpus **basse résolution** — 796×998 contre 5060×6708. L'extraction du
masque d'encre, calibrée sur des lignes de 38 px, ne transfère pas à des
lignes de 15 px.

Aucun des deux ne satisfait le critère. Le proportionnel est régulier mais
plafonne à 85 % ; le DP est excellent ou catastrophique.

## Revue de littérature — ce qui fonde le backlog

**Tesseract** (Smith, *An Overview of the Tesseract OCR Engine*) :
1. un **détecteur de pas fixe** tourne d'abord, et deux algorithmes de
   segmentation en mots existent selon sa décision ;
2. les blancs sont mesurés **dans une bande verticale limitée, entre ligne de
   base et ligne médiane** — pas sur toute la hauteur ;
3. les espaces proches du seuil sont rendus **flous** et tranchés *après*
   reconnaissance.

→ Mon DP projette toute la hauteur : jambages et accents comblent les blancs.
C'est probablement la cause de l'effondrement BNL.

**Kraken** : sait sortir ALTO/PAGE avec boîtes de mots **et positions de coupe
des caractères**, via l'alignement CTC. Route directe, mesurée par `hans` à
99,7-99,9 % — mais hors domaine sur le Fraktur (H1 réfutée).

**Alignement texte-image par DTW** (Likforman-Sulem et al., survey IJDAR ;
Kornfield et al.) : aligner mot à mot une image et sa transcription par
*dynamic time warping* sur des profils simples — projection, profil de mot,
transitions fond/encre. DTW y bat SSD et la distance euclidienne.

→ Piste forte et non essayée ici : **rendre** le texte connu dans une fonte à
l'échelle estimée, calculer son profil d'encre, et l'aligner par DTW sur le
profil observé. Donne une correspondance par caractère sans recognizer
entraîné, donc sans problème de domaine.

**Rendu synthétique** : la littérature l'emploie pour fabriquer des paires
texte-image alignées. Ici on l'emploierait à l'inverse — comme gabarit
d'alignement.

## Backlog — par ordre de promesse

| # | piste | fondement |
|---|---|---|
| B1 | blancs mesurés dans la bande **ligne de base → ligne médiane** | Tesseract |
| B2 | masque d'encre **adaptatif à la basse résolution** | échec BNL |
| B3 | **DTW gabarit rendu ↔ profil observé** | survey IJDAR, Kornfield |
| B4 | détection de **pas fixe** + algorithme dédié | Tesseract |
| B5 | classification des blancs par **Otsu sur leur distribution** | Tesseract (seuil flou) |
| B6 | **CTC kraken** — positions de coupe des caractères | hans H2/H7 |
| B7 | **Viterbi** avec modèle de largeur par caractère | classique |
| B8 | combinaison + arbitrage, y compris par VLM | hans (second moteur) |

---

## Itération 1 — 2026-09-25

### B1 · blancs en bande verticale (Tesseract)

Projeter l'encre sur **toute** la hauteur de ligne détruit le signal : hampes et
jambages du mot voisin comblent le blanc. En ne projetant que la bande dense
(corps des minuscules) pour détecter les blancs, tout en gardant le masque
complet pour l'étendue verticale des boîtes :

| corpus | inkgap DP | **band_gaps** |
|---|---|---|
| PetitParisien | 95,89 % | **98,53 %** |
| BnF | 97,19 % (max 10,72c) | **98,05 %** (max **5,93c**) |

Confirmé. Gain net là où l'encre est lisible, et le pire cas de BnF est divisé
par deux. La littérature avait raison et mon implémentation initiale avait tort.

### Le vrai résultat de l'itération : la VT de BNL n'est pas géométrique

BNL restait à 27 %. J'allais chercher la cause dans le boxer. L'overlay a montré
des boîtes VT qui chevauchent deux mots et flottent au-dessus du texte. Mesure :

| corpus | encre **dans** la boîte | encre dans le **blanc** | blancs vides |
|---|---|---|---|
| PetitParisien | 0,561 | 0,020 | 50 % |
| BnF | 0,321 | 0,000 | **100 %** |
| **BNL** | 0,184 | **0,179** | **7 %** |

**Les blancs inter-mots de BNL contiennent autant d'encre que ses boîtes.**
Sa VT donne le bon TEXTE — elle a servi à mesurer un CER de 1,9 % en Fraktur —
mais ses boîtes de mots ne délimitent rien. Noter un boxer contre elle, c'est
mesurer avec une règle faussée.

C'est la leçon de `hans` H7 (*« ce corpus ne peut pas répondre à la question »*)
appliquée à la géométrie, et je ne l'avais pas appliquée d'emblée.

**Conséquence** : `corpora.gt_is_geometric()` filtre désormais les pages dont les
blancs ne sont pas vides. Le banc passe de 1151 à 660 lignes, toutes vérifiables.

### État contre le critère gelé

| | PetitParisien | BnF | BNL (résidu) | seuil |
|---|---|---|---|---|
| ≤0,5c | 98,53 % ✅ | 98,05 % ✅ | 36,07 % ❌ | ≥95 % |
| pire cas | 7,07c ❌ | 5,93c ❌ | 8,99c ❌ | ≤3c |
| IoU médian | 0,835 ✅ | 0,919 ✅ | 0,0 ❌ | ≥0,80 |

**Aucun candidat ne passe.** Le pire cas est le mur : ≤ 0,5c sur 98 % des
frontières, mais des sorties à 6-9 caractères subsistent. Le critère fait son
travail — une moyenne excellente masquait exactement ça.

### Ajouté au backlog par cette analyse

- **B9** — trouver un corpus de substitution basse résolution / Fraktur à VT
  géométrique valide. BNL couvrait cette matière ; sans lui le banc n'a plus que
  de la presse française bien imprimée.
- **B10** — attaquer le pire cas plutôt que la médiane : identifier les lignes à
  erreur > 3c et les caractériser (mots très courts ? ponctuation isolée ?
  ligatures ?).

---

## Itération 2 — 2026-09-25

### B10 · où est le pire cas

Sur 3 516 frontières, **22** dépassent 3 caractères. Elles ne sont pas réparties :

- 16/22 sur les pages BNL résiduelles
- **55 % impliquent un mot de ≤ 2 caractères**
- les pires sont des **tableaux** : «972»|«50», «457»|«25», «id.......»|«457»

Ce ne sont pas des lignes de prose. Le pire cas est un problème de *matière*,
pas de réglage.

### B3 · DTW sur gabarit rendu — la percée

Le texte est connu : on le rend dans une fonte à l'échelle de la ligne et on
aligne son profil d'encre sur l'observé par DTW. Les frontières sont exactes
dans le rendu ; le chemin les transporte.

| | ≤0,5c | pire cas | IoU |
|---|---|---|---|
| band_gaps | 97,07 % | 8,99c | 0,897 |
| **render_dtw** | **98,12 %** | **2,25c** (BnF) | 0,789 (PP) |

Le pire cas de BnF passe de 5,93c à **2,25c** — sous le seuil pour la première
fois. Mais l'IoU du Petit Parisien tombe à 0,789 : les intervalles viennent des
avances de la fonte, approches latérales comprises.

### B11 · recalage des boîtes sur l'encre

On garde les frontières du DTW et on rétracte chaque boîte sur l'encre présente
dans son intervalle.

| corpus | ≤0,5c | pire cas | IoU | verdict |
|---|---|---|---|---|
| Petit Parisien | **99,12 %** | **1,32c** | **0,837** | ✅ ✅ ✅ |
| BnF | **99,39 %** | **1,84c** | **0,919** | ✅ ✅ ✅ |
| BNL 0015 | 32,79 % | 8,99c | 0,0 | ❌ |

**Deux corpus sur trois passent tous les seuils gelés.**

### B5 · Otsu sur les blancs — mesuré, écarté

96,3 % ≤0,5c mais **pire cas 30,0c** sur le Petit Parisien, contre 1,32c pour
B11. Contraindre les frontières à tomber sur un blanc de la classe haute casse
les lignes où Otsu sépare mal. Écarté : le critère interdit d'aggraver le pire
cas.

### Ce qui reste, et pourquoi

La page BNL 0015 est un **tableau financier** — `Luxembourg 141 Dép...... fr.
12315 31`, colonnes chiffrées et points de conduite. Sa VT est géométriquement
**valide** (0,018 d'encre dans les blancs, 51 % vides) : ce n'est pas une règle
faussée, c'est un échec réel.

**Cause identifiée** : le gabarit rend un espace uniforme entre les mots. Un
tableau a des blancs larges et très variables, et la bande de Sakoe-Chiba
(`band_frac=0.25`) interdit au DTW la déformation qu'il faudrait.

### Ajouté au backlog

- **B12** — estimer le ratio d'espace du gabarit sur les blancs observés au lieu
  de la chasse de la fonte, et élargir la bande DTW quand la variance des blancs
  est forte. Cible directe du cas tableau.
- **B13** — points de conduite (`Dép......`) : suite de composantes identiques
  régulièrement espacées ; le DTW les aligne mal car le rendu n'en produit pas le
  même nombre. À détecter et traiter comme un seul intervalle.

---

## Itération 3 — 2026-09-25

Cible : la page BNL 0015, tableau financier, seul corpus restant sous le critère.

### B12 · espace estimé + bande élargie — RÉGRESSION, écarté

| | PP pire cas | BnF pire cas | BNL |
|---|---|---|---|
| B11 (champion) | 1,32c | **1,84c** | 32,79 % |
| B12 | 1,62c | **3,37c** ❌ | 34,43 % |

BnF passe au-dessus du seuil de 3c pour 1,6 point gagné sur BNL. C'est
exactement le schéma que le critère interdit, et celui qui a réfuté H1 dans
`hans`. Écarté comme remplaçant global.

### B13 · points de conduite — n'a jamais déclenché

Chiffres identiques à B12 au centième. Diagnostic : le motif est trouvé dans le
**texte** sur 17 lignes sur 18 (`id.......`, `Dép......`), et **jamais dans
l'image** — mon seuil « petite plage » valait 5 px pour des points qui en font 7
à cette résolution. Détection côté image trop fragile.

### B14 · routage par la dispersion des blancs — sans effet

Reproduit exactement B11. La dispersion des blancs observés ne dépasse jamais le
seuil sur les lignes de tableau : elles repartent vers le moteur de prose.
Aucune régression, aucun gain. **Mauvais discriminant.**

### B15 · routage par le TEXTE — retenu

Le signal fiable était sous la main : la sortie du VLM **dit ce qu'elle est**.
Points de conduite, majorité de jetons numériques, jetons très courts sans
ponctuation de phrase.

| corpus | lignes classées tabulaires |
|---|---|
| Petit Parisien | 2/104 |
| BnF | 20/538 |
| BNL | **17/18** |

| | ≤0,5c | pire cas | IoU |
|---|---|---|---|
| Petit Parisien | 99,12 % | **1,32c** | 0,837 ✅ |
| BnF | 99,35 % | **1,84c** | 0,919 ✅ |
| BNL | 34,43 % | 8,99c | 0,0 ❌ |

**Champion préservé, gain sur BNL, zéro régression.** C'est le même principe
qu'une couche plus haut : le modèle lit, la géométrie place — ici le texte
annonce la nature de la ligne, la géométrie s'y adapte.

### Ce que l'overlay a montré

Les colonnes du tableau sont séparées par des blancs **inégaux entre eux** :
large après le nom de commune, étroit entre deux chiffres. Un `space_ratio`
scalaire, même estimé sur l'observé, impose un vide uniforme et ne peut
correspondre qu'à un seul des blancs réels. B12 était donc condamné par
construction, pas par réglage.

### B16 · espaces élastiques — en cours

Cesser de deviner la largeur des vides : rendre le texte avec des espaces
minimaux et élargir la bande de Sakoe-Chiba. Vide du gabarit et vide de l'image
sont tous deux sans encre ; le chemin DTW les apparie à coût quasi nul et peut
étirer arbitrairement — si la bande le lui permet. L'alignement découvre la
largeur des blancs au lieu qu'on la lui impose.

### B16 · espaces élastiques — DÉGRADE, écarté

BNL 34,43 → **24,59 %**, pire cas 8,99 → 11,88c. Élargir la bande de
Sakoe-Chiba à 0,90 donne au DTW la liberté d'absorber les grands vides — et
celle de divaguer. Le problème n'était pas la largeur de bande.

### Vérification écartée : les mots sont bien sur une seule rangée

Hypothèse testée avant d'aller plus loin : la « ligne » de tableau mélange-t-elle
des rangées ? **Non** — étendue des centres y de 1 à 3 px, contre 7 à 15 px sur
du Petit Parisien. Ce sont de vraies lignes visuelles.

Mais leur géométrie dit autre chose : `Luxembourg` finit à x=100, le mot suivant
commence à x=256. **Un vide de 250 px sur une ligne haute de 31 px** — 40 % de
la largeur, 8 fois la hauteur. Le DTW doit comprimer 250 colonnes observées sur
une dizaine de colonnes de gabarit.

### B17 · ancres sur les vides certains — DÉGRADE PARTOUT, écarté

| | PP pire cas | BnF pire cas | BNL |
|---|---|---|---|
| champion | **1,32c** | **1,84c** | 34,43 % |
| B17 | 5,25c ❌ | 4,88c ❌ | 27,87 % ❌ |

L'idée était juste — un vide de 250 px est une frontière certaine, autant
l'imposer que la faire redécouvrir. **L'exécution ne l'était pas** : la
répartition des mots entre segments se fait au prorata de leur largeur rendue.
J'ai réintroduit la répartition proportionnelle — la ligne de base que tout ce
travail existe pour battre — un cran plus haut, au niveau du segment.

Leçon : une ancre géométrique ne vaut que si l'affectation des mots qu'elle
sépare vient elle aussi de l'observation.

### Bilan du cas tabulaire — cinq échecs, cinq causes distinctes

| | cause identifiée |
|---|---|
| B12 espace estimé | un scalaire ne décrit pas des blancs inégaux |
| B13 points de conduite | détection côté image trop fragile (seuil 5 px / points 7 px) |
| B14 dispersion | mauvais discriminant, ne déclenche jamais |
| B16 espaces élastiques | bande large = liberté de divaguer |
| B17 ancres | affectation des mots redevenue proportionnelle |

Seul B15 (routage par le texte) a apporté un gain sans régression.

---

## Itération 5 — 2026-09-25

### B6 · CTC kraken — la route mesurée par `hans`

Deux modèles présents localement : `catmus-print-fondue-large` (celui de `hans`,
99,9 % de frontières justes sur *Le Temps*) et **`german_print`** — précisément
ce qui manquait à H1, où un recognizer d'imprimé français s'effondrait sur du
Fraktur luxembourgeois.

Principe : un CTC associe chaque symbole émis à une colonne de l'image ; les
positions de caractères sont un **sous-produit de la reconnaissance**, pas un
ajustement a posteriori. Ici le texte vient du VLM, pas du CTC : on aligne la
prédiction du CTC sur le texte connu par distance d'édition et on transporte les
frontières de mots à travers cet alignement. **Le CTC ne fournit que la
géométrie, jamais le texte** — ce qui met la contamination hors jeu.

Mise en œuvre : kraken vit dans son propre venv (Python 3.11), le banc dans
celui de MLX. OpenCV installé côté kraken plutôt qu'un pont entre interpréteurs ;
`src/run_kraken.py` exécute le même juge, sur les mêmes corpus.

Premier essai sur une ligne : 10 mots, 10 boîtes, écarts de +1 à +12 px à gauche
mais **−10 à −16 px à droite** — j'utilisais le *centre* de la coupe du dernier
caractère au lieu de son bord. Corrigé.

| | ≤0,5c | pire cas | IoU | échecs |
|---|---|---|---|---|
| champion `routage` | 98,18 % | 1,32c (PP) | **0,837** | 0 |
| **B6 `ctc_kraken`** | **99,67 %** | **0,66c** (PP) | 0,635 ❌ | 32 |

**Les meilleures frontières du banc, le pire IoU.** Diagnostic sur une ligne :
« le » fait 11 px de large contre 29 dans la VT, « Bon » 40 contre 68. Les
`cuts` de kraken sont des tranches au **centre** des caractères, pas leur
étendue — et mon recalage sur l'encre ne pouvait que rétrécir une boîte, jamais
l'élargir.

→ **B19** : le CTC ne donne plus les boîtes mais les **séparateurs** ; l'encre
entre deux séparateurs donne l'étendue. Chacun apporte ce qu'il sait faire.

---

## Itération 6 — 2026-09-25

### B19 · CTC séparateurs + étendue par l'encre

Le CTC cesse de donner les boîtes, il donne les séparateurs ; l'encre entre deux
séparateurs donne l'étendue.

| | ≤0,5c | pire cas PP | IoU PP | échecs |
|---|---|---|---|---|
| B6 boîtes du CTC | 99,67 % | 0,66c | 0,635 ❌ | 32 |
| **B19 séparateurs** | 99,65 % | **0,66c** | **0,829** ✅ | 32 |

L'IoU passe de 0,635 à 0,829 **sans déplacer une seule frontière**. Les trois
seuils de précision sont franchis sur les deux corpus valides. Restent les 32
lignes en échec.

### B20 · composition — NOUVEAU CHAMPION

Les échecs du CTC ne sont pas aléatoires. Exemple mesuré sur BnF :
`bles. L r s personnes dont ces chemins des` — une ligne dégradée dont les
jetons ne s'alignent sur aucune prédiction. Le DTW, lui, n'a pas de domaine et
tient encore.

On ne choisit donc pas : le CTC passe d'abord, le DTW reprend ce qu'il laisse.
Aucun seuil assoupli — c'est la **couverture** qui est complétée.

| corpus | ≤0,5c | pire cas | IoU | échecs | verdict |
|---|---|---|---|---|---|
| Petit Parisien | **99,41 %** | **1,32c** | **0,828** | **0** | ✅ ✅ ✅ ✅ |
| BnF | **99,64 %** | **1,96c** | **0,915** | **0** | ✅ ✅ ✅ ✅ |
| BNL 0015 | 34,43 % | 8,99c | 0,0 | 0 | ❌ |

Ligne de base proportionnelle, pour mémoire : 86,0 % et 3,38c.

C'est la même leçon qu'une couche plus haut, où deux lecteurs indépendants
valaient mieux qu'un seul : ici **deux placeurs indépendants**, dont les
domaines d'échec ne se recouvrent pas.

---

## Itération 7 — 2026-09-25

### B9 · un vrai corpus de remplacement, et une confirmation gênante

| corpus | encre boîte | encre blanc | blancs vides | pages valides |
|---|---|---|---|---|
| Petit Parisien | 0,543 | 0,018 | 55 % | 1/1 |
| BnF | 0,316 | 0,000 | 99 % | 1/1 |
| **Newseye** | 0,272 | **0,013** | **64 %** | **7/8** |
| BNL (37 p.) | 0,175 | 0,175 | 8 % | 0/8 |
| **BNLfull (1814 p.)** | 0,176 | **0,179** | **9 %** | **0/8** |

**BNLfull confirme sur 1814 pages ce que les 37 laissaient soupçonner** : les
boîtes de mots de cette vérité terrain ne sont pas géométriques, quel que soit
l'échantillon. Ce n'est pas un tirage malheureux, c'est une propriété du corpus.
Newseye — presse française, PAGE XML avec `Word` et coordonnées — le remplace.

### Revue de littérature tardive, et ce qu'elle corrige

Question du mainteneur : *« es-tu sûr de ne pas enfoncer des portes ouvertes ? »*
Vérification faite, **la réponse est en partie non**, et elle aurait dû venir
avant l'implémentation.

Le problème porte un nom — *ground-truth alignment*, **alignement forcé
transcription-image** — et une méthode établie : alignement au niveau ligne,
puis **alignement forcé au niveau caractère** pour produire les boîtes.

| brique | statut réel |
|---|---|
| B1 blancs en bande verticale | repris de Tesseract, cité |
| **B6/B19 alignement CTC** | **méthode standard — réimplémentée, pas inventée** |
| B20 composition en cascade | ingénierie courante |
| B3 DTW sur gabarit rendu | variante peu documentée (le rendu synthétique sert d'ordinaire à *fabriquer* des données à boîtes connues, pas à *aligner*) |

Outils existants vérifiés : **Transkribus Text2Image** aligne au niveau
**ligne**, pas au mot ; **Aletheia** est semi-manuel ; `ketos align` n'existe pas
dans kraken.

**Ce qui reste propre à ce travail n'est donc pas la méthode mais la mesure :**
critère gelé avant toute expérience, filtre de validité de la vérité terrain
— qui vient d'écarter 1814 pages —, notation par distribution, et le constat que
CTC et DTW échouent sur des ensembles de lignes disjoints, ce qui justifie leur
composition.

À corriger dans le README : ne pas présenter comme une trouvaille ce qui est
l'application d'une méthode documentée.

### Le banc élargi corrige une impression trop favorable

Champion `compose` sur 5 corpus (916 lignes, 4 899 frontières) :

| corpus | ≤0,5c | pire cas | IoU | verdict |
|---|---|---|---|---|
| BnF | **100,0 %** | **0,47c** | 0,897 | ✅ ✅ ✅ |
| Petit Parisien | 99,26 % | 1,32c | 0,827 | ✅ ✅ ✅ |
| **Newseye** | 97,87 % | **7,45c** ❌ | **0,610** ❌ | échec |
| BNL / BNLfull | 34,43 % | 8,99c ❌ | 0,0 ❌ | échec |

**Ajouter un vrai troisième corpus fait tomber deux seuils.** Le champion
généralisait moins bien que les deux premiers ne le laissaient croire — c'est
exactement ce que la recherche de couverture devait révéler, et la raison pour
laquelle un critère par corpus vaut mieux qu'une moyenne.

Note de banc : un mode rapide (`BBVLM_MAX_LIGNES`) borne le nombre de lignes par
page pour itérer — les pages Newseye portent 800 à 900 lignes et le CTC est lent.
La validation finale se fera sans borne.

---

## Itération 9 — 2026-09-25

### B22 · l'étendue verticale ne peut pas déborder la ligne

Diagnostic Newseye : frontières justes à 97,9 % **mais IoU 0,610**. Les
abscisses coïncidaient au pixel près (75 contre 74, 128 contre 128) ; les
hauteurs non — **54 px prédits contre 31 dans la VT, 74 % de trop**.

Cause : `ink.line_mask` élargit le crop de 12 % de la hauteur de ligne pour ne
pas trancher hampes et jambages. Utile pour **trouver** l'encre du mot, néfaste
pour **mesurer** son étendue : la marge capte l'encre des lignes voisines.

Correction : deux masques pour deux usages. Le masque élargi donne les colonnes
d'encre, un masque borné à la boîte de ligne donne l'étendue verticale.

| corpus | IoU avant | IoU après |
|---|---|---|
| Petit Parisien | 0,827 | **0,933** |
| BnF | 0,897 | **0,937** |
| Newseye | 0,610 | **0,749** |

Aucune frontière déplacée — c'était bien un problème de hauteur, pas de coupure.

### État contre le critère

| corpus | ≤0,5c | pire cas | IoU | verdict |
|---|---|---|---|---|
| BnF | 100,0 % | **0,47c** | **0,937** | ✅ ✅ ✅ |
| Petit Parisien | 99,26 % | **1,32c** | **0,933** | ✅ ✅ ✅ |
| Newseye | 97,87 % | 7,45c ❌ | 0,749 ❌ | échec |

Newseye reste à 0,05 point d'IoU et surtout à 7,45c de pire cas. Les deux
manques sont distincts : l'IoU est un problème d'étendue résiduelle, le pire cas
un problème de placement sur quelques lignes.

---

## Itération 10 — 2026-09-25

### Diagnostic Newseye — la boîte de ligne est trop lâche

| page | IoU | largeur préd/VT | hauteur préd/VT |
|---|---|---|---|
| 0250199 | 0,587 | 1,13× | **1,30×** |
| 0253902 | 0,738 | 1,07× | 1,00× |

Mesure structurelle du corpus :

```
boîte de ligne médiane 43 px   mots médiane 27 px   ratio 1,5×
28 chevauchements verticaux sur 40 lignes
```

Les boîtes de lignes Newseye font **une fois et demie la hauteur des mots** et
se chevauchent. B22, qui borne l'étendue à la boîte de ligne, capte donc encore
l'encre des voisines sur les pages les plus serrées.

### B23 · étendue par le profil d'encre — DÉGRADE PARTOUT, écarté

| corpus | IoU `serre` | IoU B23 |
|---|---|---|
| Petit Parisien | **0,933** | 0,723 ❌ |
| BnF | **0,937** | 0,675 ❌ |
| Newseye | **0,749** | 0,651 ❌ |

Chercher la région dense contiguë autour du pic, arrêtée aux creux à 18 % du
maximum, **coupe les hampes et les jambages** qui appartiennent au mot. Le
remède est pire que le mal : une boîte de ligne trop lâche reste une meilleure
borne qu'un profil trop serré.

`serre` (B22) reste champion.

### Ce que ça indique pour la suite

Le bon levier n'est ni la boîte ni le profil, mais les **composantes connexes** :
l'encre d'une ligne voisine forme des composantes distinctes, dont le centre est
loin du centre de la ligne. `ink.line_mask` filtre déjà sur ce critère
(`|Δy| > 0,85 × hauteur`) — c'est ce seuil qu'il faut resserrer, pas inventer un
nouveau mécanisme.

### B24 · resserrer le filtre existant — NOUVEAU CHAMPION

Application de la leçon payée trois fois : régler le mécanisme en place plutôt
qu'en ajouter un. `ink.line_mask` écartait déjà les composantes dont le centre
s'éloigne de plus de 0,85 × la hauteur de ligne ; sur Newseye, dont les boîtes
valent 1,5 fois la hauteur des mots, ce seuil laissait passer les voisines.
Seuil porté à 0,45 — une hampe reste centrée même en dépassant, une ligne
voisine non.

| corpus | IoU `serre` | IoU **B24** | seuil |
|---|---|---|---|
| Newseye | 0,749 ❌ | **0,815** ✅ | 0,80 |
| BnF | 0,937 | **0,939** ✅ | |
| Petit Parisien | 0,933 | 0,875 ✅ | |

Le Petit Parisien recule de 0,058 mais reste largement au-dessus ; son pire cas
ne bouge pas (1,32c). Newseye franchit le seuil.

### État contre le critère — un seul manque sur tout le banc

| corpus | ≤0,5c | pire cas | IoU | échecs |
|---|---|---|---|---|
| BnF | 100,0 % ✅ | **0,47c** ✅ | 0,939 ✅ | 0 ✅ |
| Petit Parisien | 99,26 % ✅ | **1,32c** ✅ | 0,875 ✅ | 0 ✅ |
| Newseye | 97,87 % ✅ | **7,45c** ❌ | 0,815 ✅ | 0 ✅ |

**Onze seuils sur douze sont franchis.** Reste le pire cas de Newseye — et
comme ses frontières sont justes à 97,9 %, il ne s'agit que de quelques lignes.

---

## Itération 12 — 2026-09-25

### B25 · alignement forcé CTC — le défaut signalé était réel

Critique reçue et **vérifiée dans le code** : `ctc.py` demandait d'abord au
recognizer *quelle* transcription il préfère (`rec.prediction`), puis raccrochait
cette lecture au texte du VLM par `difflib.SequenceMatcher`. Ce n'est pas de
l'alignement forcé, c'est **l'appariement de deux lectures** — et quand elles
divergent, il n'y a plus rien à quoi s'accrocher. D'où les 32 échecs, tous sur
des lignes dégradées (`bles. L r s personnes dont ces chemins des`).

L'alignement forcé ne pose jamais cette question. Il prend la matrice de
probabilités, construit le graphe CTC de la transcription **imposée** — blank,
c1, blank, c2… avec les transitions propres aux caractères répétés — et cherche
par Viterbi le chemin qui explique le mieux CE texte. Le réseau peut n'avoir que
0,42 sur un caractère : le chemin global s'en accommode là où un décodage glouton
aurait produit autre chose.

C'est la méthode de PERO (`core/force_alignment.py`), **documentée** — pas une
trouvaille de ce dépôt. `kraken` expose `forward()`, donc la matrice est
accessible ; seul mon usage était en cause.

**Un piège rencontré :** le codec écarte silencieusement les caractères hors
alphabet — le « é » de `Débats` n'est pas dans CATMuS-Print, et 21 caractères
donnent 20 codes. Encoder le texte d'un bloc casse la correspondance
position↔code. Il faut encoder caractère par caractère et garder la table.

Premier essai, écarts à la vérité terrain :

```
le       917-945   VT 917-946    (1 px)
Journal  959-1093  VT 959-1094   (1 px)
des     1106-1154  VT 1106-1155  (1 px)
le      1300-1330  VT 1300-1330  (exact)
```

Ce qui reste de BBVLM et qu'on garde : les positions CTC servent de
**séparateurs**, pas de bords de glyphes (B19 : IoU 0,635 → 0,829 sans déplacer
une frontière), et l'étendue vient de l'encre.

---

## Itération 13 — 2026-09-25 — recadrage : le VLM mérite-t-il cette plomberie ?

### B25 · alignement forcé CTC — ÉCHOUE, cause identifiée

| | échecs | ≤0,5c | pire cas |
|---|---|---|---|
| `ctc_span` (ancienne branche) | 32 | 99,65 % | 0,66c |
| **B25 alignement forcé** | **82** | 87,25 % | 23,77c |

La méthode est la bonne — imposer le texte plutôt que demander sa lecture au
réseau — mais **mon implémentation projette les frames linéairement sur la boîte
de ligne**, alors que kraken reconnaît sur une bande **rectifiée** avec un
padding de 16 px. PERO applique la transformation inverse de son extraction ; je
ne l'ai pas fait. Le test sur une ligne horizontale pleine largeur masquait
exactement cette erreur.

Leçon annexe : faire tourner un OCR pour n'en garder que les coordonnées oblige
à **répliquer sa géométrie interne**. La plomberie coûte plus cher qu'elle n'en
a l'air.

### La question qu'on n'avait jamais posée

Douze itérations à optimiser des boîtes sans mesurer **si le VLM méritait cette
plomberie**. Les deux bancs étaient aveugles l'un à l'autre : celui des boîtes
ignorait le texte, ceux du CER ignoraient les boîtes.

La vraie question n'est pas « quelle méthode fait les meilleures boîtes » mais
**« à quel moment le gain textuel du VLM justifie une seconde brique
géométrique ? »** Si un recognizer lit à 2,1 % et donne déjà un bon ALTO, bâtir
tout ceci pour 0,2 point serait absurde.

`src/banc_couple.py` mesure désormais texte ET géométrie sur les mêmes lignes.

**Premier résultat — kraken (CATMuS-Print) sur Newseye, 120 lignes :**

| page | CER |
|---|---|
| 0250199-004 | 13,17 % |
| 0253902-003 | 7,80 % |
| 0400970-002 | 6,89 % |
| **moyenne** | **9,28 %** en 14 s |

C'est le régime « 8-15 % sur du patrimonial difficile » qui rendrait
l'architecture défendable — à condition que le VLM fasse nettement mieux sur les
mêmes lignes. Mesure en cours.

### Une propriété du DTW que je n'avais pas formulée

Le DTW sur gabarit rendu **n'effectue aucune seconde reconnaissance** : il reçoit
image + texte et rend de la géométrie, sans jamais demander à un réseau ce qu'il
croit lire. C'est le seul candidat du banc dans ce cas, et il fait 99,26 % à
1,32c.

Ce n'est donc pas une solution de repli mais **l'architecture la plus cohérente
avec l'hypothèse de départ**. Le CTC sert surtout à établir la borne haute
accessible avec un signal neuronal caractère↔image.

### La mesure qui manquait — et elle ne soutient PAS la prémisse sur ce corpus

Texte, mêmes pages, mêmes lignes :

| page | lignes en entrée VLM | kraken CTC | churro VLM |
|---|---|---|---|
| 0250199-004 | 47 px | 13,17 % | 13,80 % |
| 0253902-003 | **23,9 px** | 7,80 % | *286,34 %* |
| 0400970-002 | 51,3 px | **6,89 %** | **17,89 %** |
| moyenne | | **9,28 %** | 106,01 % |
| temps | | **14 s** | 1 339 s |

**À écarter :** la page à 286 % est un artefact du harnais — ses 40 premières
lignes traversent plusieurs colonnes, le crop fait 4774 px de large et le
redimensionnement écrase les lignes à 24 px. Mesure invalide.

**À retenir :** sur 0400970, churro reçoit des lignes de 51 px — résolution
comparable à celle où il atteignait 0 % sur le Petit Parisien — et fait
**17,89 % contre 6,89 %**. L'avantage textuel du VLM, réel sur le Fraktur BNL
(1,9 %) et sur la presse 1900 (0 %), **ne se transporte pas sur cette presse
française des années 1930**.

### Ce que ça fait à la prémisse du projet

BBVLM repose sur : *le VLM lit mieux, donc il faut lui rendre la géométrie*.
Sur Newseye, le VLM ne lit pas mieux — il lit deux fois et demie moins bien, et
95 fois plus lentement. Sur ce corpus, **kraken seul est le bon choix** : il
donne le texte ET les boîtes, sans plomberie.

L'architecture ne se justifie donc pas partout. Elle se justifie là où l'écart
textuel est réellement en faveur du VLM — Fraktur, presse 1900, graphies
anciennes — et pas ailleurs. C'est une conclusion utilisable, pas un échec : elle
dit **quand** employer BBVLM.

Reste à mesurer l'écart sur les corpus où le VLM était bon, avec le même
protocole couplé. C'est la prochaine étape, et elle vaut mieux qu'une itération
de plus sur les boîtes.

---

## Itération 14 — le domaine de validité, mesuré

Même protocole couplé, sur les corpus où le VLM était censé briller.

### Fraktur / imprimé ancien — le CTC hors domaine

| page | kraken CATMuS-Print | churro VLM |
|---|---|---|
| 0000 | 40,40 % | **26,86 %** |
| 0001 | 55,25 % | **20,55 %** |
| 0002 (français, non Fraktur) | 37,90 % | *451 %* — dérive |
| moyenne des deux pages fiables | **47,8 %** | **23,7 %** |

**Kraken s'effondre à 44,5 % sur cette matière** — c'est exactement le
hors-domaine que `hans` avait identifié en réfutant H1. Churro y fait **deux
fois mieux**.

### Presse française des années 1930 — le CTC chez lui

| page | kraken | churro |
|---|---|---|
| 0400970-002 | **6,89 %** | 17,89 % |
| 0250199-004 | **13,17 %** | 13,80 % |
| moyenne | **9,28 %** | ~15,8 % |

### Le résultat central du projet

```
                    kraken CTC    churro VLM    qui gagne
Fraktur / ancien       47,8 %        23,7 %      VLM ×2
presse 1930             9,3 %        15,8 %      CTC
presse 1900 (col. 2)       —          0,0 %      VLM
```

**L'architecture BBVLM a un domaine de validité, et il est identifiable
d'avance** : elle se justifie là où le recognizer disponible est hors de son
domaine d'entraînement — Fraktur, graphies anciennes, écritures rares — et
**pas** sur de l'imprimé mécanique récent, où un CTC bien assorti lit mieux,
95 fois plus vite, et fournit les boîtes sans plomberie.

C'est une conclusion utilisable : elle dit **quand** employer cette chaîne.

### Réserve honnête sur la stabilité

Sur 5 pages mesurées avec le VLM, **2 ont dérivé** malgré le mécanisme
anti-boucle porté à 4 tentatives — troncature de fin de ligne, puis répétition
d'une ligne antérieure. C'est le défaut structurel du VLM, déjà rencontré à
chaque étape de ce travail, et il n'est pas résolu. Un système de production
devrait le détecter (le compte de lignes et le coût d'alignement le permettent)
plutôt que l'ignorer.

---

## Un trou dans la démonstration, à nommer

La chaîne se justifie sur le Fraktur et l'imprimé ancien — c'est là que le VLM
lit deux fois mieux qu'un CTC hors domaine.

**Or c'est précisément là que je ne peux pas mesurer sa géométrie.** Les seuls
corpus Fraktur disponibles ici (BNL, BNLfull) ont une vérité terrain dont les
boîtes de mots ne délimitent rien — mesuré sur 1814 pages : 0,179 d'encre dans
les blancs contre 0,176 dans les boîtes, 9 % de blancs vides.

Le banc de boîtes ne porte donc que sur **PetitParisien, BnF et Newseye** — trois
corpus d'imprimé latin où, justement, un CTC assorti lit mieux que le VLM.

```
                    VLM utile ?   boîtes mesurables ?
Fraktur / ancien        OUI              NON
imprimé latin récent    NON              OUI
```

**Les deux moitiés de la démonstration ne se recouvrent pas.** Ce n'est pas un
défaut de la chaîne mais une lacune de corpus, et elle doit être comblée avant
toute conclusion générale : il faut un corpus d'écriture hors domaine **avec des
boîtes de mots géométriquement valides**.

C'est la limite la plus sérieuse de ce travail à ce stade, et elle prime sur une
itération de plus sur les boîtes.

---

## Itération 15 — B29 : chercher un corpus Fraktur à boîtes de mots

### Candidats examinés

| corpus | format | boîtes de mots ? |
|---|---|---|
| ATR Newseye (déjà présent) | PAGE XML + Word/Coords ✅ | mais **127 pages toutes françaises** |
| **AustrianNewspapers ONB** (UB-Mannheim) | PAGE XML + images ✅ | **313 TextLine, 0 Word** ❌ |
| Reichsanzeiger-GT | PAGE XML, 490 679 mots annoncés | à vérifier |

Le jeu autrichien est du vrai Fraktur — `Arbeiter⸗Zeitung`,
`Schwarzſpanierſtr.`, avec ſ long et tiret double oblique — et il vient de la
**même famille NewsEye** que mon corpus BnF, images comprises. Mais son
annotation s'arrête à la ligne.

### Le constat de fond

**La vérité terrain au mot est rare sur le patrimonial.** La plupart des jeux —
GT4HistOCR, AustrianNewspapers, la majorité des sorties Transkribus — s'arrêtent
à la ligne, parce que c'est ce dont un recognizer CTC a besoin pour s'entraîner.
Les boîtes de mots ne servent qu'à l'aval : ALTO, recherche plein texte,
surlignage. Peu de producteurs les annotent.

Ce n'est donc pas un manque de chance dans mes recherches, c'est une propriété
du paysage documentaire — et elle explique pourquoi ce travail manque de terrain
d'épreuve là où il serait le plus utile.

### Ce que le corpus autrichien apporte malgré tout

Il donne un **meilleur banc de TEXTE en Fraktur** que BNL : 148 pages, VT
Transkribus révisée par l'université de Mannheim, images incluses. BNL servait
de repère avec 1,9 % de CER mesuré sur 5 pages ; ONB permettra une mesure plus
sérieuse de l'écart VLM / CTC sur cette écriture.

Conservé pour cet usage, écarté pour la géométrie.

---

## Itération 16 — la mesure qui renverse la conclusion précédente

### Une injustice dans mon protocole

J'avais conclu que « le VLM gagne sur le Fraktur » en comparant churro à
**CATMuS-Print**, un modèle d'imprimé **latin**, sur de l'allemand gothique.
C'est un hors-domaine que j'avais moi-même fabriqué, pas une propriété de
l'écriture.

Le test honnête est contre `german_print`, fait pour cette matière. Sur les
mêmes 90 lignes du corpus autrichien :

| moteur | CER | temps |
|---|---|---|
| kraken **german_print** (assorti) | **1,25 %** | 9 s |
| kraken catmus-print (non assorti) | 27,55 % | 5 s |

Pages : 1,06 %, **0,00 %**, 2,70 %.

**Un CTC assorti lit le Fraktur à 1,25 %.** L'écart de 22 points entre les deux
modèles kraken n'a rien à voir avec l'écriture : il tient entièrement à
l'adéquation du modèle à la matière.

### Ce que ça fait à la conclusion de l'itération 14

Elle était formulée ainsi : *« l'architecture se justifie là où le recognizer
disponible est hors de son domaine — Fraktur, graphies anciennes »*. Le mot
« Fraktur » y est **faux** : ce n'est pas l'écriture qui met un CTC en échec,
c'est l'absence de modèle assorti.

Formulation corrigée : **l'architecture ne se justifie que lorsqu'aucun modèle
assorti n'existe pour la matière traitée.** C'est nettement plus restrictif —
et vérifiable avant d'engager quoi que ce soit : il suffit de chercher s'il
existe un modèle pour l'écriture visée.

C'est exactement la conclusion de `hans` H7, que j'ai mis deux jours à
retrouver par un autre chemin :

> *« Post-correction ou ré-OCRisation ? Cela dépend entièrement de savoir si
> l'on dispose d'un recognizer assorti à son matériel. »*

---

## Itération 17 — le recadrage qui donne sa raison d'être au projet

### Hypothèse du mainteneur : un VLM de frontière ne se trompe pas

Testée directement — je suis moi-même un VLM de frontière, donc je peux lire la
page et me noter. Corpus autrichien, 12 lignes de Fraktur :

```
lignes identiques au caractère près : 12/12
CER brut                            : 0,00 %
CER normalisé                       : 0,00 %
```

ſ longs, tirets doubles obliques `⸗`, apostrophe de `Richter's` : tout y est.
À comparer aux 1,25 % de `german_print`, pourtant assorti et excellent.

### Ce que ça change — BBVLM n'est pas un concurrent d'OCR

Jusqu'ici je mesurais BBVLM **contre** les moteurs classiques, et la conclusion
était décourageante : un CTC assorti lit mieux, 95 fois plus vite, et donne les
boîtes gratuitement.

Mais la comparaison était mal posée. Un moteur classique et un VLM de frontière
ne servent pas au même usage :

| | production de masse | production de VÉRITÉ TERRAIN |
|---|---|---|
| ce qui compte | débit, coût | **exactitude** |
| kraken assorti | ✅ 3 s/page, 1,25 % | insuffisant : 1,25 % n'est pas une VT |
| VLM de frontière | ✗ lent, coûteux | ✅ 0,00 % mesuré |

**Pour produire une vérité terrain, 1,25 % de CER ne suffit pas** — c'est
précisément ce qu'une VT doit corriger. Et le coût par page n'a pas d'importance
quand on annote quelques dizaines de pages une fois.

### Et c'est exactement le goulot identifié en B29

> *« La vérité terrain au mot est rare sur le patrimonial : la plupart des jeux
> s'arrêtent à la ligne. »*

Le manque que j'ai constaté — pas de VT au mot pour éprouver la géométrie —
**est le problème que ce système résoudrait**. Un VLM de frontière donne le
texte au caractère près ; le moteur géométrique de BBVLM lui rend des boîtes de
mots à 0,47 caractère près. Ensemble : de l'ALTO de qualité VT, produit
semi-automatiquement.

**La moitié précieuse de ce dépôt est donc le moteur géométrique**, pas la
comparaison de lecteurs. C'est lui qui n'a pas d'équivalent : Transkribus
Text2Image aligne au niveau ligne, Aletheia est semi-manuel.

### Réserves, à ne pas escamoter

1. **12 lignes.** L'échantillon est minuscule et le crop était propre et bien
   dimensionné. Rien ne dit que ça tient sur une page dégradée.
2. **La dérive n'est pas testée à cette échelle.** Churro dérivait sur 2 pages
   sur 5 ; un modèle de frontière dérive moins, mais « moins » n'est pas
   « jamais », et une VT ne tolère pas une ligne inventée.
3. **La géométrie ne vient toujours pas du VLM** — 367 px d'erreur mesurés sur
   une frontière de bloc. Le moteur d'encre reste indispensable.
4. **Un humain doit valider.** Un système de production de VT sans relecture
   n'est pas une VT, c'est une sortie d'OCR de plus.

---

## Itération 18 — la chaîne de production de VT

`src/produire.py` : image → kraken `blla` → texte VLM par blocs → boîtes →
ALTO 4.4 + overlay + `provenance.json`.

**Changement de détecteur de lignes.** La détection par pics d'encre que j'avais
écrite suppose des lignes horizontales à pas régulier — hypothèse qui tombe sur
du manuscrit ou une page gondolée. Pour un outil de vérité terrain, la
robustesse prime sur l'élégance d'avoir tout écrit soi-même : `kraken blla`
détecte des lignes de base et des polygones, et encaisse l'inclinaison.

**Les trois propriétés d'une VT sont des exigences de code, pas des intentions :**

1. *Elle refuse.* Deux contrôles sans référence — compte de mots incohérent, et
   texte inajustable à l'encre. Une ligne qui échoue est retirée de l'ALTO et
   consignée avec son motif. Le seuil se calibre sur le document traité.
2. *Elle est relue.* L'overlay distingue les lignes écartées (rouge) des lignes
   retenues (vert) et des mots (bleu).
3. *Elle déclare sa provenance.* Modèle lecteur, moteur géométrique, lignes
   détectées / retenues / écartées, **taux de relecture**, seuil employé, durée.

**Rapatriements.** `alto.py` et `correct.py` venaient de `vlm-alto-fresh` ;
`correct.py` a été réécrit pour ne dépendre que des modules d'ici. Son coût
d'ajustement mesure désormais la dispersion des largeurs observées face aux
largeurs attendues, normalisée par l'échelle estimée sur la ligne.

Première page : 2479×3508, 24 lignes détectées par kraken. Quelques
`TopologyException` du polygoniseur sur des lignes dégradées — sans effet sur la
détection, mais à surveiller.

---

## Itération 19 — qui sait lire du Fraktur, mesuré à l'aveugle

### Une erreur de protocole à signaler d'abord

Mon « 0,00 % » de l'itération 17 était **contaminé** : j'avais affiché la vérité
terrain dans la même sortie avant de transcrire. Ce n'était pas une lecture à
l'aveugle.

Reprise propre : bande jamais montrée, VT écrite dans un fichier et non
affichée, transcription, puis révélation. Résultat inchangé — **9 lignes sur 9
exactes, CER 0,00 %** — mais cette fois il vaut quelque chose.

### Le classement, sur la même bande

| lecteur | exactes | CER normalisé | durée |
|---|---|---|---|
| **VLM de frontière** (Opus 5) | **9/9** | **0,00 %** | — |
| kraken `german_print` (CTC assorti) | — | **1,25 %** | 3 s/page |
| mistral-medium-latest | 3 | 4,60 % | 3 s |
| mistral-small-latest | 4 | 4,72 % | 3 s |
| mistral-large-latest | 5 | 10,35 % | 7 s |
| mistral-ocr-latest | 0 | 184 % | 1 s |
| churro-3B | — | dérive sur 2 pages sur 5 | 22 min/page |

**Mistral ne suffit pas pour de la vérité terrain** — 4,6 % au mieux, soit
presque quatre fois pire qu'un CTC assorti. Et `mistral-ocr-latest` rend du
markdown de page entière, pas des lignes : il ne répond pas au besoin.

Note : `mistral-large` fait **moins bien** que `medium` et `small` sur cette
matière. Les modèles plus grands ne lisent pas mécaniquement mieux du Fraktur.

### Conséquence pour la chaîne

Le poste de lecteur exige une classe de modèle que l'API Mistral ne fournit pas
ici. Deux options réalistes :

1. **un modèle de frontière par API** — coûteux, mais le coût par page est sans
   importance pour produire quelques dizaines de pages de VT ;
2. **le modèle de la session lui-même** — c'est ce qui a produit les 0,00 %, et
   c'est implémentable aujourd'hui : Claude lit les bandes, le moteur
   géométrique place les boîtes.

La seconde n'est pas un artifice : elle correspond exactement à l'usage visé —
un humain (ou un agent) produit une VT sur quelques dizaines de pages, avec
relecture.

## B36 — gabarit Fraktur pour le DTW

**Question** : le gabarit rendu en Times fausse-t-il la géométrie sur du Fraktur ?

**Fait** : installé `fontes/UnifrakturCook-Bold.ttf` (Google Fonts, OFL).
UnifrakturMaguntia n'est pas récupérable (pointeur LFS). Le choix de fonte n'est
PAS un réglage : `dtw.py` rend le texte dans chaque famille disponible et retient
celle qui minimise le coût DTW normalisé, ligne par ligne. Ajouter une fonte ne
peut donc rien casser par construction — c'est ce qui rend la chose reproductible
sur un document inconnu.

**Mesuré** sur la bande Fraktur d'ONB_aze_18950706_3 (9 lignes, texte lu par moi
à 0,00 % CER), sans VT géométrique donc sur trois quantités internes :

| | encre dans les boîtes | encre dans les inter-mots | chevauchements |
|---|---|---|---|
| serif seul | 0,989 | 0,012 | 10 |
| serif + Fraktur | 0,991 | 0,010 | **16** |

Le gabarit Fraktur n'est retenu que sur 3 lignes sur 9. Là où il l'est, les
chevauchements augmentent.

**Cause** : le coût DTW n'est pas un bon mandataire de la qualité des boîtes. Il
mesure la ressemblance des deux profils d'encre ; une fonte plus grasse ressemble
mieux au Fraktur observé en densité tout en plaçant moins bien les frontières.
On optimise la ressemblance et on note le placement — ce ne sont pas la même chose.

**Conclusion** : hypothèse ÉCARTÉE. Le gabarit latin n'était pas la cause. Le
mécanisme de sélection reste en place (il ne coûte rien et documente son choix),
mais il ne faut pas lui faire dire ce qu'il ne mesure pas. Accessoirement, `dtw`
fait 10 à 16 chevauchements là où `connexe` en fait 0 : le champion reste champion.

**Reste ouvert** : la géométrie sur Fraktur demeure non mesurée faute de VT au mot
sur cette écriture. Ce n'était pas un problème de fonte.

## B37 — double lecture sur la visionneuse gt-presse-gallica

**Constat** : `~/gt-presse-gallica` contient déjà l'atelier qui manquait — 28 pages
du *Temps*, 24 680 lignes, chacune avec sa boîte (`boite`, à multiplier par
`echelle`), son OCR Gallica et sa confiance. L'interface découpe la ligne, la
grossit 2,1×, pré-remplit le champ avec l'OCR et fait relire l'humain. Actuellement
**0 annotation** : parce qu'il faut relire les 24 680 lignes.

**Protocole mesuré** : double lecture indépendante (pratique courante en production
de VT, *double keying* ; ce n'est pas une trouvaille). Lecteur A = OCR Gallica.
Lecteur B = moi, à l'aveugle sur les seules images de lignes. Accord caractère pour
caractère ⇒ ligne validée sans humain. Désaccord ⇒ l'humain tranche.

Échantillon stratifié de 18 lignes de `bpt6k2362495_f0001`, tirées 6 basses / 6
médianes / 6 hautes confiances :

- accord parfait **10/18**, désaccord 6, refus 2 (lignes sans texte que Gallica
  transcrit quand même : « V-N y », « -yc- »)
- CER de Gallica contre ma lecture : **6,72 %**
- des 12 lignes à wc ≥ 0,9 : 10 accords, et les 2 écarts sont un point doublé et
  un tiret doublé — artefacts d'encodage, pas des lectures divergentes
- des 6 lignes à wc < 0,9 : 6 à relire

Repondéré par la distribution réelle du corpus (67,5 % des lignes à wc ≥ 0,9) :

> **taux de relecture humaine 32 à 44 %** — contre 100 % aujourd'hui.

**Ce que ça change** : l'humain ne relit plus la page, il arbitre les désaccords.
Le gain est d'un facteur 2 à 3, mesuré, pas estimé. Et la géométrie au mot arrive
gratuitement : la ligne a déjà sa boîte, `connexe` y place les mots, la VT sort en
ALTO au mot au lieu de texte au niveau ligne.

**Limite** : la strate haute n'a que 12 lignes d'échantillon ; l'intervalle de
confiance sur 2/12 est large. Il faut porter l'échantillon à ~100 lignes avant
d'annoncer un chiffre ferme. Et l'accord de deux lecteurs ne prouve pas la
justesse — deux lecteurs peuvent se tromper pareil sur une abréviation d'époque.
C'est pour ça que l'accord vaut *présomption*, et que la provenance doit dire
quelles lignes ont été vues par un humain et lesquelles ne l'ont pas été.

## B38 — double lecture : écartée, mais elle a révélé un défaut de normalisation

Piste explorée puis abandonnée : elle répondait à une question hors projet (le
texte doit venir du VLM seul, pas d'un consensus d'OCR). Ce qu'elle laisse :

Kraken catmus-print sur les 1035 lignes d'une page du *Temps* (139 ms/ligne),
confronté à l'OCR Gallica : 50,0 % d'accord. En arbitrant 16 désaccords à
l'aveugle, 5 sur 16 n'étaient **pas** des désaccords de lecture mais d'encodage —
Gallica aplatit le `SUBS_TYPE` d'ALTO en doublant le tiret de césure (`Raf--`),
kraken sort le `¬` philologique. Ma fonction `norm` ne les canonisait pas.

Corrigé dans `src/double_lecture.py` (césure en fin de ligne, espace fine française
avant la ponctuation haute — sans toucher à la casse, aux accents ni à l'identité
des signes). Accord 50,0 % → **65,7 %** sur les mêmes 1035 lignes, sans qu'aucun
lecteur ne change. 46 % des désaccords restants portent sur un seul caractère.

**Leçon** : j'ai failli conclure « les deux lecteurs divergent » là où ils lisaient
la même chose. Toute mesure d'accord entre outils patrimoniaux doit d'abord
prouver que sa normalisation ne compte pas des conventions.

## B39 — l'œil du VLM comme juge binaire des boîtes : instrument faible

24 mots de BnF et PetitParisien, boîtes de `connexe` en surimpression, VT cachée,
échantillon stratifié sur l'erreur réelle (seuils absolus : <0,10 / 0,10-0,50 / ≥0,50).
Jugement binaire bon/mauvais.

- accord avec la VT : **19/24 = 79 %**
- rappel 62 % (3 mauvaises boîtes laissées passer), précision 71 %
- erreur médiane de ce que je valide 0,14 car., de ce que j'accuse 0,67 car.

Les populations se séparent, mais rater 4 mauvaises boîtes sur 10 interdit de
certifier quoi que ce soit. **Causes** : la planche est affichée réduite de moitié,
et surtout un verdict binaire jette toute l'information métrique.

## B40 — lire les frontières sur une règle graduée : percée

Au lieu de juger, relever. On surimprime une règle graduée sur la bande de ligne
et le VLM lit les graduations où le mot commence et finit — *Set-of-Mark
prompting* (Yang et al. 2023), documenté, pas une trouvaille. La tâche passe
d'une estimation de coordonnées (où les VLM sont mauvais, c'est le verrou du
projet) à une lecture (où ils sont bons).

9 mots, échantillon stratifié sur l'erreur de `connexe`. Aucune boîte n'est
montrée — la lecture ne peut pas copier le moteur. 3 mots tronqués par un défaut
de découpe (marge bornée par `line_box` au lieu de l'image ; corrigé).

Sur les 6 mots mesurables :

| | erreur médiane | pire cas | ≤ 0,5 car. |
|---|---|---|---|
| `connexe` | 0,69 car. | 1,14 | 50 % |
| **VLM sur règle** | **0,08 car.** | **0,28** | **100 %** |

Et sur les trois mots où `connexe` est le plus faux (1,01 / 1,14 / 1,05), le VLM
est à 0,04 / 0,05 / 0,07. Il corrige précisément là où le moteur échoue.

**Réserves** : 6 mots, c'est un indice, pas une mesure — il faut 100 mots avant
d'annoncer un chiffre. L'échantillon sur-représente volontairement les échecs de
`connexe` (1/3 tiré au-dessus de 0,5 car.), donc les 50 % de `connexe` ne sont pas
son taux réel (96,65 % sur corpus complet) ; en revanche cela ne biaise pas la
mesure du VLM, qui lit l'image et pas la sortie du moteur. Et neuf lectures ont
coûté neuf regards : à l'échelle d'une page ce n'est pas tenable en aveugle.

**Suite (B41)** : `connexe` a-t-il un signal interne qui prédit ses propres
échecs ? S'il existe, la chaîne devient praticable — le moteur place tout, le
signal désigne les boîtes douteuses, le VLM ne remesure que celles-là sur règle.
C'est là que se joue « des boîtes parfaites ».

## B41 — `connexe` ne sait pas quand il se trompe : piste ÉCARTÉE

21 100 mots (Newseye, PetitParisien, BnF), sept indices calculables sans VT :
largeur observée sur largeur attendue, encre coupée au bord de la boîte, blanc
disponible à gauche et à droite, creux interne le plus profond, densité, marge.

| indice | AUC |
|---|---|
| droite | 0,651 |
| marge | 0,627 |
| r_larg | 0,611 |
| dens | 0,608 |
| gauche | 0,598 |
| bord | 0,572 |
| creux | 0,547 |
| **combinaison (7)** | **0,663** |

Router 20 % des mots ne rattrape que 42 % des mauvaises boîtes (le hasard en
rattraperait 20 %). **Le routage par le doute ne tient pas.**

**Cause** : ces indices décrivent la géométrie locale de l'encre — exactement ce
dont `connexe` se sert déjà pour placer la boîte. Ils ne peuvent pas être
indépendants de sa décision. Un signal utile devrait venir d'ailleurs : du texte
(longueur attendue du mot), ou d'un second moteur de nature différente.

## Correction de métrique — mes mesures B39 à B41 ne sont pas celles de CRITERE.md

`judge.py` note la **frontière entre deux mots consécutifs** et la compte juste si
elle tombe n'importe où dans le blanc de la VT. B39, B40 et B41 notaient l'écart
de **chaque bord de boîte au bord du mot** — bien plus sévère. D'où « 25 % de mots
au-dessus de 0,5 car » en B41 contre 96,65 % sous le seuil au banc : ce ne sont
pas les mêmes grandeurs.

Les comparaisons moi / `connexe` restent valides (même règle des deux côtés) mais
aucun de ces chiffres n'est comparable au critère gelé. `src/regle_ligne.py` note
désormais sous les deux, nommément.

## B42 — relevé sur règle à l'échelle de la ligne : échec instructif

Une planche par mot coûte un regard par mot : inutilisable. Ici la règle couvre
la ligne, découpée en deux segments d'environ trois mots.

Ligne de BnF, 6 mots. Sous la métrique gelée : moi 100 % ≤ 0,5 car (pire 0,35),
`connexe` 100 % (pire 0,00). Sous la métrique stricte : moi médiane 0,42 car,
`connexe` **0,04**. Le moteur écrase le VLM sur cette ligne.

**Cause, mesurée** : l'erreur n'est pas dans l'œil mais dans le comptage.

```
segment a : biais -0,01 car, dispersion 0,13 car
segment b : biais -0,41 car, dispersion 0,32 car
            pas ajusté 10,07 px contre 10 déclaré  -> échelle juste à 0,7 %
            origine ajustée 3269 contre 3259       -> décalée d'exactement 1 graduation
```

Sur la planche dense (64 graduations, un chiffre tous les 5) l'origine a été lue
une graduation trop loin, et tout le segment a glissé. Le segment aéré est, lui,
excellent : biais nul, dispersion 0,13 caractère.

**Corrigé** : `planche()` chiffre chaque graduation tant que la place le permet
(un sur deux au-delà de 34, un sur cinq au-delà de 70), répète les chiffres sous
la bande, et marque l'origine d'une barre noire pleine qu'aucun trait rouge ne
peut imiter.

**Ce que ça dit du projet** : le relevé sur règle est précis (0,13 caractère de
dispersion) mais fragile au repère. C'est une erreur d'instrument, pas de mesure —
donc réductible. À vérifier au prochain tir sur les mêmes lignes.

## B42 bis — la contrainte de lisibilité de la règle, mesurée

En comparant les deux segments de la même ligne, lus par le même œil :

| | graduations | px par graduation sur la planche | dispersion du relevé |
|---|---|---|---|
| segment a | 41 | **34 px** | 0,13 car |
| segment b | 64 | **22 px** | 0,32 car |

Ce n'est ni la longueur des mots ni la densité de caractères : c'est
l'**écartement des graduations sur la planche rendue**. En dessous d'environ
30 px le comptage devient faux. `ECART_MIN = 30` et `PAS_CAR = 0,33` sont
désormais des constantes nommées de `regle_ligne.py`, et `decouper()` en déduit
le nombre de mots par planche — il n'est plus choisi à la main.

Vérifié aussi, parce que l'hypothèse aurait tout changé : **la VT colle l'encre**
(écart médian VT→encre 0,00 car à gauche, −0,04 à droite sur les 6 mots de la
ligne). La métrique stricte mesure donc bien une justesse de boîte et non une
convention d'annotation. Hypothèse écartée proprement.

**Le vrai coût** : 4 planches pour 6 mots, soit un regard pour 1,5 mot. Le relevé
sur règle ne peut donc pas remplacer le moteur — seulement le rattraper là où il
échoue. Et B41 dit qu'on ne sait pas où.

## B43 — le doute doit venir d'ailleurs que du moteur

B41 a échoué pour une raison structurelle, pas conjoncturelle : ses sept indices
décrivaient la géométrie locale de l'encre, c'est-à-dire *exactement ce dont
`connexe` se sert pour décider*. Un indice calculé sur la décision ne peut pas
être indépendant d'elle.

Piste en cours : le **désaccord entre moteurs de natures différentes** (connexe,
inkgap, proportional, serre, profil) comme signal. C'est le comité de requête de
Seung, Opper & Sompolinsky (1992), standard en apprentissage actif — documenté,
pas une trouvaille. Écart-type et étendue des bords proposés par le comité,
notés en AUC contre le seuil de 0,5 caractère, puis taux de capture en routant
5/10/20/30 % des mots vers la règle.

## B44 — dépistage visuel à l'échelle de la ligne (préparé)

`src/depistage.py`. B39 avait fait juger 24 vignettes sur une planche unique que
l'afficheur réduisait de moitié : rappel 62 %. Ici une planche par ligne (ou par
groupe de mots), boîtes numérotées, et deux garde-fous :

- `HAUTEUR_MIN_MOT = 26` px : sous cette hauteur rendue, `planche()` renvoie
  `None` au lieu d'une image. Refuser de montrer vaut mieux que recueillir un
  avis sur du flou — c'est la même règle que le refus d'une ligne dans une VT.
- `decouper(min_px_par_mot=110)` : chaque mot doit disposer d'au moins 110 px
  rendus, sinon ses bords ne sont pas visibles. Le nombre de mots par planche en
  découle, il n'est pas choisi.

Le dépistage ne mesure pas, il TRIE. Ce qu'il désigne part au relevé sur règle,
qui mesure. Cascade, pas remplacement. À mesurer : rappel et précision contre la
VT, sur un échantillon moitié lignes sales moitié lignes propres.

## Note d'exploitation — mémoire

La machine a 16 Go et le banc à cinq moteurs sur trois pages par corpus l'a
saturée (67 Mo libres, plusieurs tâches de fond tuées par le système). Le banc
DTW multi-gabarit, lancé en B36 et sans résultat après plus d'une heure, a été
arrêté : il n'est pas sur le chemin critique puisque `connexe` reste champion.
Le multi-gabarit reste à vérifier sur un échantillon réduit avant d'être déclaré
sans régression. À ne pas oublier : **c'est une vérification due, pas faite.**

## B45 — le champion tournait deux fois trop lentement, et c'était ma faute

En cherchant pourquoi B43 ne rendait rien après une heure, chronométrage des
moteurs sur BnF : `connexe`, `serre` et `profil` à 380-400 ms par ligne, et
**exactement le même temps** — signe d'une étape commune, pas d'un algorithme lent.

Première hypothèse, fausse : `line_mask` repeignait le masque en balayant tout le
tableau d'étiquettes une fois par composante retenue. Corrigé par une table de
correspondance appliquée en un passage (sortie vérifiée rigoureusement
identique), mais la fonction ne coûtait que 10 ms. **Ce n'était pas là.**

Profilage au lieu de devinette. Le coût est dans `dtw_path`, atteint par
`connexe` → `compose` → `routage` → `dtwsnap` → `dtw`. Et il était appelé **deux
fois par ligne au lieu d'une** : c'est ma sélection multi-gabarit de B36 qui
rendait le texte dans chaque fonte disponible. J'avais doublé le coût du champion
pour un gabarit que B36 avait lui-même montré inutile.

Deux corrections :

1. **Gabarit unique par défaut.** Le mécanisme de sélection reste, désarmé ;
   `BBVLM_FONTES=toutes` le rallume pour le mesurer. Ajouter une fonte ne doit
   pas coûter au champion tant qu'on n'a pas montré qu'elle sert.
2. **Vectorisation du DP.** La ligne de coût et les deux minima venant de la ligne
   précédente se calculent d'un coup ; seule la récurrence sur `D[i, j-1]` reste
   séquentielle. 8,9 millions d'appels Python à `min` et `abs` par douze lignes
   disparaissent.

**400 → 119 ms par ligne, 3,4×.** Tout le dépôt en profite : chaque banc, chaque
mesure, chaque itération de la boucle.

**Vérification en cours** : le banc doit retrouver exactement les chiffres connus
de `connexe` (96,65 % ≤ 0,5 car, IoU 0,839, 0 échec). Une accélération qui change
une sortie n'est pas une accélération. Tant que ce banc n'a pas rendu, la
vectorisation est **non validée**.

## B46 — la non-régression de B45, et un doute sur le chiffre du champion

Le banc après vectorisation ne rend pas les chiffres enregistrés :

| corpus | champion enregistré | après B45 |
|---|---|---|
| BnF | 100 % ≤0,5c, pire 0,47, IoU 0,939 | 99,35 %, pire 1,84, IoU 0,945 |
| PetitParisien | 99,26 %, pire 1,32, IoU 0,875 | 99,12 %, pire 1,32, IoU 0,897 |
| Newseye | 97,87 %, pire 7,45, IoU 0,815 | 94,77 %, pire 33,31, IoU 0,867 |

Deux hypothèses : la vectorisation a changé le DP, ou le périmètre a changé.

**La vectorisation est disculpée par mesure directe** : 60 paires de profils
aléatoires (longueurs 20 à 260, amplitudes variées), chemin comparé à
l'implémentation d'origine recopiée telle quelle. Écart maximal **0**. Les deux
codes rendent le même chemin, bit pour bit.

**Le périmètre, lui, a bougé** : le corpus compte aujourd'hui 9 pages Newseye et
7586 lignes sur les 8263 du banc. Le chiffre global du champion (96,65 %) n'a
donc pas été obtenu sur ce corpus-là. Mais BnF est une page unique de 538 lignes :
si BnF bouge, c'est autre chose qu'un périmètre.

**Vérification lancée** : le même banc avec le `dtw.py` du commit 33f35c3, soit
avant toute modification de B36 et B45. Si BnF y donne aussi 99,35 %, alors c'est
le chiffre enregistré dans `state.json` qui est faux ou daté, et non le code.

**Leçon de méthode, à retenir** : un chiffre de référence qui ne porte pas la
trace du périmètre sur lequel il a été obtenu n'est pas une référence. `state.json`
enregistre `pct05` et `iou` sans le nombre de pages ni de lignes. À corriger —
sinon toute non-régression future butera sur la même ambiguïté.

## Incident — le commit B46 a annulé la vectorisation de B45

Pour le banc de contrôle j'avais remplacé `src/boxers/dtw.py` par la version du
commit 33f35c3. La restauration était écrite à la suite de la commande d'attente,
laquelle a été mise en arrière-plan avant de l'atteindre : elle ne s'est jamais
exécutée. Le `git add -A` du commit B46 a donc enregistré l'ancienne version
par-dessus la nouvelle, sans que rien ne le signale — `git status` était propre,
puisque le fichier correspondait bien à ce qui venait d'être committé.

Détecté en vérifiant que le fichier courant contenait bien le code de B45 plutôt
qu'en le supposant. Restauré depuis `git show 489ebc2:src/boxers/dtw.py`, vérifié
identique à la sauvegarde `/tmp/dtw_apres.py`.

**Deux règles qui en sortent :**

1. Ne jamais faire tourner un banc sur une version de fichier différente de celle
   du dépôt sans l'isoler — copie du module dans un répertoire temporaire, ou
   `git stash`, jamais une substitution en place dans l'arbre de travail.
2. `git add -A` après avoir substitué un fichier est un piège silencieux. Un
   commit qui suit une manipulation de fichiers doit énumérer ses chemins.

## B47-B48 — le chiffre du champion était mesuré sur un corpus tronqué

**B47, comparaison directe.** Les 538 lignes de BnF, boîtes calculées deux fois :
une fois avec le `dtw.py` du commit 33f35c3 chargé depuis un répertoire séparé,
une fois avec celui d'aujourd'hui. Chaque exécution imprime le chemin du module
qu'elle a réellement importé, pour que la comparaison ne repose pas sur une
supposition.

> **538 lignes identiques sur 538, zéro différence.**

B36 et B45 n'ont rien changé à la géométrie. Le code est disculpé.

**B48, la vraie cause.** `run.py` lit `BBVLM_MAX_LIGNES`, qui tronque le nombre de
lignes notées par page. En le faisant varier sur BnF :

| max_lignes | lignes notées | ≤0,5c | pire | IoU |
|---|---|---|---|---|
| 20 | 20 | 100 % | 0,02 | **0,939** |
| 40 | 40 | 100 % | 0,39 | 0,941 |
| 100 | 100 | 100 % | 0,39 | 0,940 |
| aucune | **538** | **99,35 %** | **1,84** | 0,945 |
| *champion enregistré* | *non consigné* | *100 %* | *0,47* | ***0,939*** |

L'IoU du champion tombe exactement sur celui du banc tronqué à 20 lignes.

> **Les chiffres du champion ont été obtenus sur quelques dizaines de lignes par
> page, et présentés comme s'ils portaient sur le corpus.**

Ce n'est pas un détail de comptabilité. CRITERE.md était réputé tenu sur onze
seuils sur douze ; ce jugement reposait sur un banc tronqué. Sur le corpus
complet, Newseye passe de 97,87 % à 94,77 % et son pire cas de 7,45 à 33,31
caractères — il échoue alors trois critères sur quatre, et le banc compte une
ligne en échec là où le champion en annonçait zéro.

**Ce qui a permis de le voir** : avoir refusé de conclure d'un écart entre
chiffres agrégés, et être allé comparer les sorties ligne à ligne. L'écart de
chiffres était réel mais ne disait rien de sa cause.

**Ce qui l'avait caché** : un chiffre de référence sans son périmètre. Corrigé —
`run.py` imprime et enregistre désormais pages et lignes par corpus.

## B49 — l'état réel du champion, et un doublon de corpus

**Doublon.** BNL et BNLfull rendaient des chiffres rigoureusement identiques
(7,056 / 8,99 / 34,43 % / IoU 0,0), ce qui avait l'air de deux confirmations
indépendantes. Même md5 : le sous-ensemble `cinoc/corpus/37-GT-BNL` est
entièrement contenu dans le téléchargement BNL complet. **37 pages comptaient
double.** `all_pages()` déduplique désormais par contenu (taille + empreinte des
64 premiers Kio) et annonce ce qu'elle écarte.

Vérifié avant d'accuser la mesure : sur la page BNL, les boîtes de la VT collent
l'encre et ne sont pas dégénérées. L'IoU médian de 0,0 est donc un vrai échec de
`connexe` sur ce tableau financier, pas un décalage de coordonnées.

**L'état réel de `connexe`**, corpus complet, sans troncature :

| corpus | ≤0,5c ≥95 % | pire ≤3c | IoU ≥0,80 | vs proportionnel |
|---|---|---|---|---|
| BnF (538 l.) | 99,35 ✓ | 1,84 ✓ | 0,945 ✓ | 1,84 / 3,38 ✓ |
| PetitParisien (104 l.) | 99,12 ✓ | 1,32 ✓ | 0,897 ✓ | 1,32 / 2,14 ✓ |
| Newseye (7586 l.) | 94,77 ✗ | **33,31** ✗ | 0,867 ✓ | **33,31 / 28,60** ✗ |
| BNLfull (18 l.) | 34,43 ✗ | 8,99 ✗ | 0,000 ✗ | **8,99 / 2,79** ✗ |

> **9 seuils tenus sur 16. Deux corpus conformes sur quatre.**
> Et non « onze sur douze », qui était le chiffre d'un banc tronqué.

**Le plus grave** : `connexe` viole la clause de non-régression contre le
proportionnel sur Newseye (33,31 contre 28,60) et sur BNLfull (8,99 contre 2,79).
C'est exactement la clause qui avait fait réfuter `hans` H1 — « un gain moyen qui
dégrade un corpus n'est pas un gain ». Le champion du dépôt tombe sur son propre
critère, et personne ne l'avait vu parce que le banc s'arrêtait aux premières
lignes de chaque page.

**Conséquence pour B40.** La règle graduée donnait 0,08 caractère médian contre
0,69 pour `connexe` sur six mots. Je lisais ce résultat comme « le VLM bat un
moteur excellent ». Il faut le relire comme « le VLM bat un moteur dont on ignorait
qu'il échouait ». L'écart reste réel — même règle des deux côtés — mais sa portée
change : il ne s'agit plus de gratter les derniers pour cent, il s'agit de
rattraper des échecs francs. À porter à ~100 mots avant d'en tirer quoi que ce soit.

## B51 — l'aiguillage vers le moteur de tableau se déclenche sur de la prose

Deux constats en lisant le chemin de décision de `connexe`, avant toute mesure.

**`connexe` ne touche pas aux frontières horizontales.** Il reprend les boîtes de
`Compose` et ne corrige que leur étendue verticale. Les chiffres de frontières
qu'on lui attribue (≤0,5 car, pire cas, et donc la clause de non-régression)
sont ceux de `Compose` ; la contribution propre de `connexe` est l'IoU. Le nom de
« champion des boîtes » recouvre donc deux choses qu'il faut cesser de confondre.

**`routage.est_tabulaire` a une troisième règle qui ne tient pas.** Après les
points de conduite et la part de jetons numériques, elle déclare tabulaire toute
ligne dont 70 % des mots font trois caractères ou moins et qui ne contient ni
virgule, ni point-virgule, ni deux-points, ni guillemet fermant. Mesuré :

| corpus | lignes routées vers le moteur de tableau | dont par la règle « mots courts » |
|---|---|---|
| Newseye | 191 / 7586 (2,5 %) | **90** |
| BnF | 20 / 538 (3,7 %) | **17** |
| PetitParisien | 2 / 104 | 2 |
| BNLfull | 17 / 18 (94,4 %) | 0 — points de conduite, correct |

Et voici ce que la règle attrape :

```
« punisse je rie vendrai pas mon âme »
« De nombreux toast ont été po. tés par le »
« Corse dont le nom a été mis en avant par »
« de la sollicitude du gouvernement de la »
« Le calcul est fondé sur ce que le 31 décem- »
```

C'est de la prose française ordinaire. La règle se déclenche parce que le
français est fait de mots outils courts — *de, la, le, du, à, et, en, que, ce,
par*. Le commentaire de B15 disait « le texte dit ce qu'il est » ; il le dit pour
les points de conduite et les colonnes de chiffres, pas pour la brièveté des mots.

Le moteur de destination, `DTWAdapt`, avait été mesuré en B12 comme dégradant le
pire cas de BnF de 1,84 à 3,37 caractères — c'est pourquoi il avait été écarté
comme moteur principal. Il reste atteint par cette porte dérobée.

**Hypothèse à quantifier (B52, script prêt)** : ce mauvais aiguillage est un
contributeur au fait que `connexe` fasse pire que le proportionnel sur Newseye.
Le script compare les deux moteurs sur les seules lignes concernées.

## B50 — `connexe` contre le proportionnel sur Newseye : la clause tombe sur UNE frontière

9629 frontières où au moins un des deux moteurs dépasse 0,5 caractère :

| seuil | connexe | proportionnel |
|---|---|---|
| > 0,5 car | 2 168 | 8 699 |
| > 1 car | 1 350 | 4 460 |
| > 3 car | 464 | 991 |
| > 10 car | 59 | 103 |
| médiane | **0,00** | 0,94 |
| p90 | **1,44** | 3,08 |
| p99 | **7,90** | 10,26 |
| max | 33,31 | **28,60** |

`connexe` est meilleur sur 8125 frontières et pire sur 1403. Il domine à **tous**
les quantiles, y compris p99. La clause de non-régression de CRITERE.md est
violée par **une seule frontière sur 45 195**.

CRITERE.md reste GELÉ — on ne rature pas un critère parce qu'on le rate. Mais le
fait doit être dit avec sa distribution : un maximum sur 45 000 tirages n'est pas
une statistique robuste, et le préambule du critère demandait justement de
regarder p90 et p99. Ici les deux sont nettement favorables à `connexe`.

**Hypothèse réfutée en chemin** : je pensais que les pires cas venaient d'une VT
dégénérée (largeur de caractère estimée à 1 px, donc erreur normalisée énorme).
Seulement 13 des 464 cas ont une largeur de caractère sous 10 px, et la
corrélation entre `1/cw` et l'erreur n'est que de +0,137. Le pire cas est dans
une plage de largeur parfaitement normale.

## B52-B53 — la vraie cause du pire cas : de l'encre étrangère dans la boîte de ligne

Le pire cas, regardé et non supposé. Page 0253902-003, ligne 468, texte
« ouvrier . » — une fin de paragraphe.

```
boîte de ligne VT : 2541 -> 3364        (le filet de colonne est vers 3340)
boîtes VT         : ouvrier 2542-2671 | . 2692-2698
boîtes connexe    : ouvrier 2542-3330 | . 3353-3363
```

La boîte de ligne **déborde dans la colonne voisine**. L'encre du « d » de
« dans » entre dans le support, le moteur étire son gabarit de deux mots sur
toute l'étendue, et place le second mot dans l'autre colonne. Ce n'est ni un
défaut de la VT des mots (elle est juste) ni du bruit : c'est une boîte de ligne
qui franchit un filet, et un moteur qui fait confiance à son support.

**Mesure en cours (B53)** : combien de lignes ont un support d'encre bien plus
large que ne l'exige leur texte ? L'indice n'utilise que le texte et l'image,
jamais la VT des mots — il est donc utilisable en production.

## B53-B57 — l'encre étrangère, et pourquoi il ne fallait pas de détecteur

**B53, prévalence.** Support d'encre rapporté à l'étendue du texte :

| corpus | médiane | p99 | max | > 1,2× |
|---|---|---|---|---|
| Newseye | 1,00 | 1,18 | 15,87 | 70 / 7585 (0,9 %) |
| BnF | 1,00 | 1,03 | 1,03 | 0 |
| PetitParisien | 1,00 | 1,00 | 1,00 | 0 |

Rare, mais c'est de là que vient toute la queue extrême.

**B54, première version ÉCARTÉE.** Rogner d'après un seuil sur la largeur du
support corrigeait bien le cas visé (boîtes à un pixel de la VT) et améliorait
les 70 lignes suspectes, mais **dégradait BnF** : pire cas 1,84 → 9,04, 34
frontières touchées là où B53 ne mesurait aucune pollution. Le seuil comparait le
support à la largeur du gabarit *rendu en Times*, grandeur dépendante de la fonte
et sans rapport avec le texte imprimé.

**B55, le détecteur n'existe pas.** Cherché une règle sur deux grandeurs
disponibles sans VT — support rapporté au nombre de caractères et à la hauteur du
corps, et largeur du plus grand blanc interne. Les distributions se recouvrent :

| règle | suspectes attrapées | saines abîmées |
|---|---|---|
| A=1,5 B=2,0 | 32 / 70 | 94 / 8157 |
| A=2,0 B=2,0 | 22 / 70 | 46 / 8157 |
| A=3,0 B=3,0 | 11 / 70 | 16 / 8157 |

Aucun réglage ne donne une séparation exploitable. **Piste du détecteur abandonnée.**

**B56, le principe qui marche : ne pas décider.** On propose au DTW les supports
candidats — entier, et tronqué à chaque amas d'encre — et on garde celui dont le
coût d'alignement normalisé est le plus faible. Le gabarit porte la forme du
texte ; si l'encre étrangère le contrarie, le support rogné s'aligne mieux. Aucun
seuil à régler, décision prise ligne par ligne sur une quantité que le moteur
calcule déjà.

| | `connexe` | `rogne` |
|---|---|---|
| Newseye, 175 frontières polluées | méd. 0,31 · p90 7,45 · max 33,31 · ≤0,5c 53,1 % | méd. 0,00 · p90 **2,40** · max 29,30 · ≤0,5c **73,7 %** |
| BnF, contrôle (2773 frontières) | 99,4 % · max 1,84 | 99,4 % · max 1,84 — **1 frontière change sur 2773** |
| PetitParisien, contrôle (682) | 99,1 % · max 1,32 | **682 / 682 identiques** |

Et le cas qui avait tout déclenché :

```
VT      : ouvrier 2542-2671 | . 2692-2698
connexe : ouvrier 2542-3330 | . 3353-3363   (second mot dans l'autre colonne)
rogne   : ouvrier 2543-2670 | . 2692-2697   (à un pixel près)
```

**Banc complet en cours** — ces chiffres portent sur un sous-ensemble choisi, ils
ne valent pas verdict tant que le corpus entier n'a pas parlé.

## B52 — le mauvais aiguillage est réel et ne coûte rien : on ne corrige pas

B51 avait montré que `routage.est_tabulaire` déclare tabulaire de la prose
française ordinaire (90 lignes de Newseye, 17 de BnF) à cause de sa règle
« 70 % de mots de trois caractères ou moins ». L'hypothèse était que ce mauvais
aiguillage contribuait aux échecs de Newseye, `DTWAdapt` ayant été mesuré en B12
comme dégradant BnF de 1,84 à 3,37.

Mesuré sur les seules lignes concernées, les deux moteurs comparés sur les mêmes
frontières :

| | moteur prose (DTWSnap) | moteur tableau (DTWAdapt) |
|---|---|---|
| Newseye, 90 lignes, 552 frontières | ≤0,5c 84,8 % · p90 0,97 · max 11,09 | ≤0,5c **85,5 %** · p90 1,05 · max **9,95** |
| BnF, 17 lignes, 105 frontières | ≤0,5c **100 %** · max **0,00** | ≤0,5c 99,0 % · max 0,81 |

**Hypothèse infirmée.** Sur Newseye le moteur reçu à tort fait légèrement mieux ;
sur BnF il coûte une frontière, sur un corpus dont le pire cas global (1,84) vient
d'ailleurs. Supprimer la règle dégraderait Newseye pour gagner un cas sur BnF.

**Décision : ne rien changer.** La règle reste conceptuellement fausse — elle sera
notée au backlog pour le jour où un corpus la rendra coûteuse — mais modifier du
code sur une théorie que la mesure contredit serait exactement l'erreur que ce
journal existe pour empêcher. B12 avait mesuré le coût de `DTWAdapt` comme moteur
*principal*, sur toutes les lignes ; il ne se transporte pas à 107 lignes choisies
par un motif textuel.

## B57 — `rogne` au banc complet : ÉCARTÉ, et pourquoi

| corpus | `connexe` | `rogne` |
|---|---|---|
| BnF (538 l.) | 99,35 / 1,84 / 0,945 | **identique** |
| PetitParisien (104 l.) | 99,12 / 1,32 / 0,897 | **identique** |
| Newseye (7586 l.) | 94,77 / 33,31 / 0,867 | 94,29 / **30,78** / 0,866 |
| BNLfull (18 l.) | 34,43 / 8,99 / 0,000 | **27,87 / 17,75** / 0,000 |

Le gain sur le pire cas de Newseye est réel (−2,53 caractères) mais s'accompagne
d'une perte de 0,48 point sur les frontières, et surtout d'un **effondrement sur
BNL** : pire cas presque doublé.

**Cause.** BNL est un tableau financier. Un blanc large y est une structure de
colonne, pas de la pollution. L'arbitrage par coût DTW préfère le support court
parce que le gabarit est rendu comme une prose : le moteur coupe précisément ce
qu'il fallait garder. Le mécanisme n'est pas faux, son domaine d'application l'est.

**Ce que ça confirme sur la méthode** : le corpus de contrôle avait bien joué son
rôle sur BnF et PetitParisien, où `rogne` est resté rigoureusement inerte. Mais je
n'avais pas mis BNL dans le contrôle — je l'avais écarté mentalement comme « cas
dur déjà connu ». Un corpus qu'on renonce à améliorer doit rester dans le contrôle,
justement parce qu'on n'y regarde plus.

## B58 — rognage réservé aux lignes non tabulaires

`routage.est_tabulaire` reconnaît 17 des 18 lignes de BNL par leurs points de
conduite (mesuré B51). On s'en sert comme garde : sur une ligne tabulaire, `rogne`
rend la main à `connexe` sans toucher au support. Aucun nouveau mécanisme, aucun
seuil supplémentaire — on réutilise un détecteur dont le domaine de validité est
déjà mesuré. Banc complet en cours.

## B58 — le garde tabulaire marche, mais `rogne` reste un échange

| corpus | `connexe` | `rogne` sans garde | `rogne` + garde |
|---|---|---|---|
| BnF (538 l.) | 99,35 / 1,84 / 0,945 | identique | **identique** |
| PetitParisien (104 l.) | 99,12 / 1,32 / 0,897 | identique | **identique** |
| BNLfull (18 l.) | 34,43 / 8,99 / 0,000 | 27,87 / 17,75 / 0,000 | **34,43 / 8,99 / 0,000** |
| Newseye (7586 l.) | 94,77 / 33,31 / 0,867 | 94,29 / 30,78 / 0,866 | 94,35 / **30,78** / 0,866 |

Le garde fait exactement ce qu'on lui demandait : BNL revient au chiffre près, et
le gain sur Newseye est conservé. Réutiliser un détecteur dont le domaine de
validité était déjà mesuré (17 lignes de BNL sur 18) a coûté trois lignes de code
et n'a introduit aucun réglage.

**Mais le compte reste un échange** : pire cas −2,53 caractères, frontières
−0,42 point. CRITERE.md place le taux de frontières en premier, et Newseye échoue
de toute façon dans les deux cas. **`connexe` reste champion.** `rogne` est
conservé dans le dépôt comme mécanisme validé et documenté, pas promu.

**Piste laissée ouverte, non explorée** : `GAIN_MIN` (0,02) est la marge que doit
gagner le support rogné pour être préféré. L'augmenter ferait moins de rognages à
tort. Mais la régler sur Newseye reviendrait à l'ajuster sur le corpus qui sert à
la noter — il faudrait un corpus de réglage distinct, qui n'existe pas ici.
Inscrit au backlog plutôt que fait à moitié.

## B60 — le relevé sur règle à 61 mots : B40 NE TIENT PAS

B40 annonçait 0,08 caractère médian pour le VLM contre 0,69 pour `connexe`, sur
**six** mots. Porté à **61 mots** (9 lignes entièrement relevées, 30 planches),
échantillon équilibré moitié lignes où `connexe` est pris en défaut, moitié
lignes propres :

| métrique GELÉE (CRITERE.md) | médiane | p90 | max | ≤0,5c |
|---|---|---|---|---|
| VLM sur règle | 0,00 | 0,00 | **0,00** | 100 % |
| `connexe` | 0,00 | 0,00 | 0,19 | 100 % |

| métrique STRICTE | médiane | p90 | max | ≤0,5c |
|---|---|---|---|---|
| VLM sur règle | 0,12 | **0,29** | 1,81 | **95,1 %** |
| `connexe` | **0,07** | 0,52 | **1,10** | 88,5 % |

Tête-à-tête sur la stricte : VLM meilleur sur 18 mots, **pire sur 26**, égal sur 17.

**Conclusion : le résultat de B40 ne tient pas.** Sur le critère gelé, les deux
sont à égalité parfaite et le VLM n'apporte rien. Sur la stricte, il est plus
régulier (moins de mauvais cas) mais moins précis sur le mot courant, et perd le
tête-à-tête.

**Cause de l'erreur de B40** : son échantillon avait été stratifié sur l'erreur de
`connexe`, un tiers tiré au-dessus de 0,5 caractère. Sur six mots, cela revenait à
choisir ses pires cas et à les comparer à un relevé neuf. Je l'avais écrit à
l'époque — « l'échantillon sur-représente volontairement les échecs de `connexe`,
en revanche cela ne biaise pas la mesure du VLM » — ce qui était vrai pour le VLM
pris seul et faux pour la **comparaison**, qui est pourtant ce que j'en ai tiré.

**Ce que ça coûte** : 0,48 planche par mot, soit une image à regarder pour deux
mots. Pour un gain nul sur le critère gelé.

**Ce qui reste vrai et utile** : le relevé est *régulier*. Son p90 (0,29) est
meilleur que celui du moteur (0,52) et il produit moins de bords à plus de 0,5
caractère. Il n'est donc pas un remplaçant du moteur mais un possible recours sur
les cas que le moteur rate — à condition de savoir lesquels, ce que B41 a montré
qu'on ne sait pas faire.

## B44 — le dépistage visuel : haute précision, faible rappel

Huit lignes de BnF et Newseye, 57 boîtes numérotées sur 19 planches, chacune
rendue à la résolution que `depistage.py` impose (110 px minimum par mot). Boîtes
en surimpression, vérité terrain cachée. Consigne : nommer les numéros dont le
rectangle ne colle pas son mot.

```
57 boîtes, 9 réellement fausses (>0,5 car, métrique stricte)
  justesse   88 %
  précision 100 %   (B39, vignettes réduites : 71 %)
  rappel     22 %   (B39 : 62 %)
  faux positifs 0, faux négatifs 7
```

Le rappel dépend de la grosseur de la faute :

| seuil | boîtes fausses | repérées |
|---|---|---|
| > 0,5 car | 9 | 2 (22 %) |
| > 1,0 car | 3 | 2 (**67 %**) |

Les deux accusations portaient sur 1,17 et 1,77 caractère ; les boîtes validées
ont une erreur médiane de 0,14. Les sept manquées sont toutes entre 0,54 et
1,24 caractère.

**Ce que ça dit, et c'est une caractérisation plutôt qu'un échec** : l'œil du VLM
n'est pas un instrument de mesure, c'est un détecteur de fautes **catégorielles**.
Il a vu une boîte posée sur le filet de colonne et le début d'un mot de la colonne
voisine — précisément le défaut que B52 avait identifié comme source de toute la
queue extrême de Newseye, et que B41 avait montré indétectable par les statistiques
internes du moteur. Il ne voit pas un demi-caractère, ce qui est normal : à
l'échelle d'une ligne entière, un demi-caractère fait quelques pixels.

**Conséquence** : la cascade « dépistage puis relevé » ne tient pas au seuil de
0,5 caractère du critère. En revanche l'œil est le bon outil pour le défaut que
les chiffres ne savent pas trouver. Deux instruments, deux domaines — et c'est la
première fois qu'on peut le dire avec des chiffres des deux côtés.

**Limite à ne pas cacher** : 57 boîtes, 9 fausses, dont 3 au-dessus de 1 caractère.
Le rappel de 67 % au-dessus de 1 caractère repose sur trois cas. Il faut une
centaine de fautes grossières avant d'en faire un chiffre.

## B43 — le doute existe, mais hors du moteur : AUC 0,824

15 145 mots (BnF, PetitParisien, 2 pages Newseye), cinq moteurs de natures
différentes placent les boîtes, et c'est leur **désaccord** qui sert de signal —
comité de requête (Seung, Opper & Sompolinsky 1992), standard en apprentissage
actif, documenté et non inventé ici.

| indice | AUC |
|---|---|
| écart-type des bords gauches | 0,755 |
| écart-type des bords droits | 0,759 |
| étendue des bords gauches | 0,755 |
| étendue des bords droits | 0,758 |
| **max des deux étendues** | **0,824** |

| part des mots routés | mauvaises boîtes rattrapées |
|---|---|
| 5 % | 17 % |
| 10 % | 33 % |
| **20 %** | **56 %** |
| 30 % | 69 % |

À comparer à B41, où sept indices calculés **à l'intérieur** de `connexe`
plafonnaient à 0,663 et ne rattrapaient que 42 % en routant 20 %.

**Ce qui distingue les deux, et c'est le point** : les indices de B41 décrivaient
la géométrie locale de l'encre, celle dont `connexe` se sert pour décider — ils ne
pouvaient pas être indépendants de sa décision. Le désaccord entre moteurs est
une quantité que le moteur seul ne peut pas produire. La cause de l'échec de B41
était la bonne, et sa correction fonctionne.

**Ce que ça n'établit pas encore** : que la cascade soit utile. B60 a montré que le
relevé sur règle ne bat pas le moteur *en général*. Il ne devient un recours que
si, **sur les mots que le comité désigne**, il fait mieux. C'est la mesure
suivante — et elle doit porter sur ces mots-là, pas sur un tirage quelconque.

## B61 — la cascade se valide : le VLM bat le moteur LÀ OÙ le comité doute

B43 donne un signal de doute (AUC 0,824). B60 dit que le relevé sur règle ne bat
pas le moteur en général. Restait la seule question qui compte : est-il meilleur
**sur les mots que le comité désigne** ?

Échantillon tiré exclusivement dans le **décile le plus disputé** (187 lignes sur
1874). Ce décile est bien le bon : l'erreur stricte médiane de `connexe` y vaut
**0,57 caractère contre 0,07 sur l'ensemble** — huit fois pire.

Six lignes relevées entièrement, 35 mots, 20 planches. Deux lignes exclues : l'une
parce que la découpe tronquait un mot, l'autre parce que son jeton de VT est un
tilde combinant et que l'encre du segment appartient à la ligne du dessous.

| métrique GELÉE (CRITERE.md), 29 mesures | médiane | p90 | max | ≤0,5c |
|---|---|---|---|---|
| VLM sur règle | 0,00 | **0,00** | 3,46 | **96,6 %** |
| `connexe` | 0,00 | 0,63 | **1,03** | 86,2 % |
| | | | VLM meilleur sur 7, pire sur 2, égal sur 20 | |

| métrique STRICTE, 35 mesures | médiane | p90 | max | ≤0,5c |
|---|---|---|---|---|
| VLM sur règle | **0,20** | **0,61** | 8,52 | **82,9 %** |
| `connexe` | 0,33 | 1,57 | **4,81** | 57,1 % |
| | | | VLM meilleur sur 15, pire sur 14, égal sur 6 | |

**B60 et B61 ne se contredisent pas, ils se complètent** : le relevé ne bat pas le
moteur sur un tirage quelconque, et le bat sur le décile disputé. C'est
exactement la condition d'existence d'une cascade.

**Réserves, à ne pas masquer :**

1. 35 mots, 6 lignes. C'est un indice fort, pas une mesure établie.
2. Le pire cas du VLM est plus mauvais (3,46 contre 1,03 ; 8,52 contre 4,81). Il
   vient des lignes dont le **texte de la VT est illisible** — `<o`, `»*`,
   `'8tl*` pour un texte qui lit « 28 62 | 28 62 » — où mon placement était une
   conjecture. Défaut de vérité terrain plutôt que de lecture, mais il compte.
3. Le décile disputé est en grande partie composé de lignes tabulaires et de
   lignes à texte dégradé. Le comité détecte donc aussi la mauvaise qualité du
   TEXTE, pas seulement la difficulté géométrique. C'est utile mais ce n'est pas
   ce qu'on croyait mesurer.

**Architecture complète et mesurée, pour la première fois :**

| étage | rôle | coût | mesure |
|---|---|---|---|
| `connexe` | place toutes les boîtes | 119 ms/ligne | 99,35 % et 99,12 % sur BnF et PetitParisien |
| comité de 5 moteurs | désigne les douteuses | 5 × le moteur | AUC 0,824, 56 % des fautes dans 20 % des mots |
| VLM sur règle | remesure celles-là | ~0,5 planche/mot | 96,6 % contre 86,2 % sur le décile |

## B62-B63 — la boucle avait été arrêtée trop tôt

L'utilisateur relève que le système ne sort pas d'ALTO parfaits et qu'aucun corpus
difficile n'a été éprouvé. Les deux sont exacts. La boucle s'était arrêtée sur la
**lettre** de sa condition — un artefact produit et la géométrie mesurée — et non
sur l'objectif, qui était des boîtes justes. Trois manques :

1. `CRITERE.md` échoue sur deux corpus sur quatre.
2. Le troisième étage n'a **jamais tourné** : les artefacts marquent les mots
   `a_remesurer` sans les remesurer. La cascade est validée sur 35 mots, pas
   exécutée.
3. Le corpus tenait en quatre documents de presse latine imprimée.

**B62 — BNL ne peut pas servir de règle, et le filtre avait raison.** 123 pages
mesurées sur les 1814 disponibles :

| | p10 | médiane | p90 |
|---|---|---|---|
| encre dans les blancs inter-mots | 0,133 | **0,167** | 0,197 |
| part de blancs réellement vides | 0,04 | **0,09** | 0,23 |

Le seuil du filtre est 0,06 d'encre et 30 % de blancs vides : 2 pages sur 123
passent. En relâchant à 0,12 / 0,15 on n'en récupère que 7. Les boîtes de cette
VT ne délimitent pas les mots — ce n'est pas une VT au mot, ce sont des boîtes
grossières. **Piste fermée, définitivement.**

**Le mur réel du projet, nommé.** Inventaire des 2442 XML du disque : la vérité
terrain **au mot** n'existe que sur de la presse latine imprimée. Le manuscrit de
Dresde (`Mscr.Dresd.K.80`, kurrent saxon de 1665, 10 pages) et le Fraktur d'ONB
n'ont qu'un `String` par `TextLine` — annotation à la ligne. Aucune règle
géométrique n'existe pour l'écriture difficile.

**B63 — le corpus dur était là et n'était pas lu.** Le jeu ATR Newseye contient
**127 pages** et le chargeur s'arrêtait à 12. Plafond levé :

| | avant | après |
|---|---|---|
| pages Newseye | 9 | **65** |
| lignes | 7 586 | **46 351** |
| mots | ~32 000 | **308 426** |

Tous les chiffres de `connexe` sur Newseye portaient donc sur un sixième du corpus
disponible. Banc complet relancé sur ce périmètre.

## B65 — la cascade EXÉCUTÉE se retourne : le quota par page est faux

Premier passage réel du troisième étage, sur les 12 mots que le comité avait
marqués dans `out-pp/`. Jusqu'ici la cascade n'avait jamais tourné : elle était
validée sur un échantillon (B61) et les artefacts marquaient sans remesurer.

| | médiane | max | ≤0,5c |
|---|---|---|---|
| `connexe` seul, sur les 12 mots marqués | **0,05** | **0,27** | **100 %** |
| après mon relevé sur règle | 0,21 | 0,86 | 75 % |

**Amélioré 2 mots, dégradé 10.**

**Cause.** En B61, le décile disputé était tiré sur tout le corpus, dominé par
Newseye où le moteur échoue : son seuil de désaccord allait de 5,29 à 33,83
caractères, et l'erreur stricte médiane de `connexe` y valait 0,57. Ici le seuil
du décile de CETTE page vaut 2,78 caractères et l'erreur médiane de `connexe` sur
les mots ainsi désignés vaut 0,05 : **il n'y avait rien à corriger**. Un quota de
10 % appliqué page par page force à remesurer des mots déjà justes, et sur un mot
facile le relevé est moins précis que le moteur — ce que B60 disait déjà
(médiane 0,12 contre 0,07).

**Ce que ça apprend sur la méthode** : valider une cascade sur un échantillon
choisi dans le régime favorable ne dit rien de son comportement en service. Il
fallait l'exécuter. C'est le manque que l'utilisateur avait relevé, et l'exécution
a immédiatement retourné le résultat.

**Correction à mesurer (B66)** : router sur un seuil ABSOLU de désaccord, calibré
une fois sur le corpus, et non sur un quantile par page. Une page propre ne doit
alors rien envoyer au troisième étage.

## A54 — 2026-09-28 — image+PERO avec garde, validation indépendante

16 blocs BnL nouveaux, figés par hash avant ouverture. PERO+A37 puis une seule
passe Luna aveugle image+candidat. CER recherche 0,933 % → 0,683 % et lexical
0,529 % → 0,311 % avec garde déterministe; aucune régression des blocs PERO
déjà exacts, portes pré-déclarées passées. Deux réécritures non reconstructibles
sont refusées. Toujours pas 0 % (82/12004 éditions search), ni boîtes parfaites
(IoU80 mot 33,54 %, français 15,81 %). Détails dans
`experiments/loop/bnl-independent-a54/RESULTS.md`.

## A55 — 2026-09-28 — diagnostic des quatre bords, garde largeur rejetée

Sur les 1 957 mots A54 appariés, A37 améliore l'IoU moyen global
0,5807→0,6685, mais l'IoU horizontal français baisse 0,8245→0,8077 et trois
blocs français régressent. Une grille pré-déclarée de plafonds d'expansion de
largeur 1,00–1,20 ne produit aucun candidat respectant la non-régression par
bloc. Aucun changement de production. Le résultat renforce la nécessité d'une
VT mot explicitement contrôlée avant de poursuivre le réglage géométrique.

## A56 — 2026-09-28 — Europeana: vraie VT région, aucune boîte mot/ligne

Audit exhaustif des 50 PAGE XML de Zenodo 2583866, archive vérifiée par MD5.
Le corpus contient 2 458 `TextRegion`, 678 séparateurs et un ordre de régions,
mais **0 `TextLine`, 0 `Word`, 0 `Glyph`**. Il est donc rejeté pour certifier les
boîtes ALTO mot/ligne, sans même télécharger 31 MB d'images. Il reste candidat
OLR/régions sous réserve d'auditer la provenance. Aucun paramètre, OCR ou VLM;
aucune page de test BBVLM consommée.

## A57 — reprise durable corrigée

Le générateur de checkpoint écrasait les entrées A54-A56 avec sa liste legacy arrêtée à A51. Rapports intacts, état récupéré par les scripts de registration. Préservation des extensions, recalcul des artefacts manquants et portes prises seulement du protocole : test de régression passé. Exécution CPU sans doublon : zéro phase restante. Sept objectifs toujours non atteints.

# A58 — audit de 801 annotations Chronicling Germany

**371 575 TextLine, 0 Word, 0 Glyph** : les mots annoncés dans le papier sont des tokens, pas des boîtes de mots. 19 343 TextRegion, 11 506 SeparatorRegion, 1 306 TableRegion, 296 GraphicRegion, 63 ImageRegion. Les 32 514 régions et 371 575 lignes actuelles diffèrent des 32 451 / 371 642 du papier : citer la révision exacte.

456 Coords et 341 Baseline contiennent des points hors des dimensions déclarées ; 8 polygones dégénérés. Aucun ID dupliqué ni référence région pendante. Ce sont des alertes structurelles, à vérifier sur les images.

Splits : 651 train, 50 validation, 100 test dont 20 OoD ; splits principaux disjoints et cinq titres OoD absents de train/validation. **Une faute dans le split officiel** : Training contient `Koelnische_ZeiOut of distributiontung_1924_0035`, absent des XML ; `Koelnische_Zeitung_1924_0035` existe mais n’est assigné à aucun split. Aucune correction silencieuse. Les 100 pages test sont réservées ; aucune image ni valeur de transcription inspectée pour cette sélection.

Source : 60 036 720 octets téléchargés ; les 801 blobs XML reconstruisent exactement l’arbre Git publié, vérifié à la révision 66b50f53ccdb581d29cc02f670e469bbf583e825. Empreintes par fichier conservées.

Décision : retenir les régions comme référence candidate, texte à auditer selon ses conventions. Ne pas certifier les boîtes de mots ni l’ordre de lecture avec ce corpus. Le papier indique double contrôle des régions, simple correction du texte, correction sélective des lignes, ordre automatique non corrigé. Statuts Transkribus : 661 IN_PROGRESS,111 DONE,13 GT,13 NEW,3 autres/absents ; ce n’est pas une certification.

Coût : ~15 s CPU, aucune passe OCR/VLM ni image téléchargée. Objectif global non atteint. Prochaine expérience : Sol sur résidus OCR A54, crops source, IDs aveugles ; développement consommé, pas nouvelle validation.


# A59 — lecture Sol native : variante rejetée

Six blocs A54 consommés, quatre résidus lexicaux élevés et deux témoins exacts. Une session gpt-6-sol, six images inspectées en détail original, aucune transcription ni référence montrée.

| Mesure | Luna guard A54 | Sol aveugle |
|---|---:|---:|
| CER lexical (sans espaces/ponctuation) | 24/4990 = 0,481 % | 57/4990 = 1,142 % |
| CER recherche | 54/6291 = 0,858 % | 74/6291 = 1,176 % |
| Témoins exacts lexical/recherche | 2/2 | 2/2 |

Le bloc 0455 (luxembourgeois ancien, italique, 893×3059 px) concentre la dégradation : 8→45 éditions lexicales. 0009 gagne5→3 ; 0345 gagne8→5 ; 0231 dégrade3→4. Ce test ne compare pas seulement les modèles : Luna avait PERO, Sol lit les pixels seuls. Il ne permet donc pas de conclure que Sol est intrinsèquement moins bon. Il rejette la substitution aveugle testée.

Audit visuel parent sur 0345 et 0455, après score : sur0345, l’image soutient clairement « la belle », « vous », « écoutez » et « votre », contre « ja belle », « vons », « éeoutez » et « vore » dans la référence. Quatre désaccords paraissent donc provenir de la référence. La présence de l’accent de « brûlant » reste à adjuger. Original XML inchangé ; ces observations ne sont pas une nouvelle GT indépendante. Sur0455, accents peu lisibles dans un bloc très haut : tester le même contenu en bandes natives courtes avant une décision sur les glyphes.

Coût : six images, zéro nouveau détecteur/OCR, tokens non exposés. IDs et empreintes contrôlés ; aucun objectif global validé. A60 prévoira une ablation de présentation par trois bandes de même source, sans modifier pixels, modèle ni consigne de transcription. Diagnostic sur bloc consommé.


# A60 — bandes natives : gain partiel, objectif non atteint

Même bloc0455, Sol aveugle : **45→36 écarts lexicaux** (4,233→3,387 %), recherche47→39 (3,268→2,712 %). Luna avec garde A54 reste à8 écarts lexicaux. La réduction de hauteur seule ne résout donc pas le défaut.

Trois bandes893×1026/1001/1032, zéro interpolation ; reconstruction exacte des pixels source vérifiée. Deux frontières inspectées visuellement : coupes dans le blanc, pas dans les caractères. Une nouvelle session Sol et trois images, aucune passe PERO. Le changement de session introduit de la variabilité : un seul essai ne prouve pas la causalité résolution. A54 reste consommé, référence inchangée.

Décision : ne pas remplacer la variante A54 par cette lecture aveugle. Prochain diagnostic : garder l’ancrage textuel A54 et ne proposer que corrections localisées justifiées sur ces bandes, avec garde reconstruction stricte. Cela teste un mécanisme de correction conditionnelle, pas une nouvelle validation ni une sélection oracle déployable.

