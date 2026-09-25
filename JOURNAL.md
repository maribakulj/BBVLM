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
