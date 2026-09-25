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
