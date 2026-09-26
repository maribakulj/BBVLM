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
