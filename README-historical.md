# BBVLM — Produire de la vérité terrain ALTO

**But : fabriquer de l'ALTO au mot de qualité vérité-terrain**, en combinant un
VLM de frontière (texte au caractère près) et un moteur géométrique (boîtes à
0,47 caractère près). Voir [OBJECTIF.md](OBJECTIF.md).

Ce n'est **pas** un concurrent des moteurs OCR : pour de la production de masse,
un CTC assorti lit à 1,25 % en 3 s/page et fournit les boîtes. Mais 1,25 % est
précisément ce qu'une vérité terrain doit corriger.

**Reconstruire des boîtes ALTO au mot, *from scratch*, à partir d'une image de
ligne et de son texte rendu par un VLM.** Pas de reconstruction naïve : le
système s'appuie sur la littérature d'alignement texte-image et sur les étages
des moteurs OCR classiques.

## Le problème

Un VLM lit très bien le patrimoine — 1,9 % de CER sur du Fraktur, 0 % sur des
passages de presse 1900 — mais **ne produit aucune coordonnée fiable** : mesuré,
367 px d'erreur sur une frontière de bloc. Il ne peut donc pas produire d'ALTO.

Inversement, les moteurs CTC placent les caractères au pixel près, mais
s'effondrent hors de leur domaine d'entraînement.

BBVLM occupe cet interstice : **le VLM lit, la géométrie place.**

## Situation dans la littérature

Le problème porte un nom — *ground-truth alignment*, alignement forcé
transcription-image — et sa méthode établie est l'**alignement forcé au niveau
caractère**. Le composant principal de BBVLM (les `cuts` d'un recognizer CTC)
en est une **application, pas une invention**.

Les outils existants ne couvrent pas exactement ce besoin : Transkribus
*Text2Image* aligne au niveau **ligne** et non au mot, Aletheia est semi-manuel,
et kraken n'expose pas de sous-commande d'alignement.

Ce que ce dépôt apporte tient donc moins à la méthode qu'à **la mesure** : un
critère gelé avant toute expérience, un filtre de validité appliqué à chaque
vérité terrain, et la composition de deux aligneurs dont les domaines d'échec ne
se recouvrent pas.

## Approche retenue — CTC pour les coupures, DTW sur gabarit rendu en repli

Le texte est connu (c'est la sortie du VLM). On le **rend** dans une fonte à
l'échelle de la ligne, on calcule le profil d'encre du rendu, et on l'aligne sur
le profil observé par *dynamic time warping*. Les frontières de mots sont
exactes dans le rendu ; le chemin DTW les transporte vers l'image. Les boîtes
sont ensuite rétractées sur l'encre réellement présente.

Aucun recognizer entraîné n'intervient — donc aucun problème de domaine.

Fondements : survey d'alignement texte-image de documents historiques
(Likforman-Sulem *et al.*, IJDAR) ; Tesseract (Smith) pour la mesure des blancs
en bande verticale limitée entre ligne de base et ligne médiane.

## Résultats

3 516 frontières, 660 lignes, corpus à vérité terrain **vérifiée géométriquement**.

| boxer | ≤ 0,5 car | pire cas | IoU médian |
|---|---|---|---|
| proportionnel *(ligne de base)* | 86,0 % | 3,38c | 0,598 |
| plages d'encre + DP | 95,9 % | 10,72c | 0,896 |
| + blancs en bande verticale | 97,1 % | 8,99c | 0,897 |
| **DTW gabarit + recalage encre** | **98,2 %** | **1,84c** | **0,898** |

Par corpus, pour le candidat retenu :

| corpus | ≤ 0,5 car | pire cas | IoU |
|---|---|---|---|
| Petit Parisien 1900 | 99,12 % | 1,32c | 0,837 |
| BnF | 99,39 % | 1,84c | 0,919 |

## Discipline de mesure

- **Le critère est gelé avant toute mesure** (`CRITERE.md`) et exige les seuils
  sur **chaque** corpus, jamais en moyenne.
- **Toute vérité terrain est vérifiée avant de servir de règle.** Un corpus dont
  les blancs inter-mots contiennent autant d'encre que ses boîtes a été écarté :
  ses boîtes ne délimitent pas les mots. Mesurer contre lui revenait à utiliser
  une règle faussée.
- La notation porte une **distribution** — p90, p99, pire cas — jamais une
  moyenne seule.
- `JOURNAL.md` consigne chaque itération, **les échecs compris**.

## Utilisation

```bash
python src/run.py dtwsnap:DTWSnap          # mesurer un boxer
python src/analyse_pire.py                 # caractériser les pires frontières
```

Un boxer reçoit l'image, le **texte** de la ligne et la **boîte de ligne**.
Jamais les boîtes de mots de la vérité terrain — celles-ci ne servent qu'à noter.

## Licence

Apache-2.0.
