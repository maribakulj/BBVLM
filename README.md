Reprise du 7 octobre : chaque OCR doit livrer l'image source et son ALTO pour
l'inspecteur de l'utilisateur. La commande complète est :

```sh
/Users/marcel/cinoc/.venv/bin/python scripts/ocr_page.py IMAGE SEGMENTATION_AUTOMATIQUE SORTIE --gemini-pane ID_VERIFIE
```

Elle conserve le Markdown libre de Gemini, puis lance l'appariement et le
placement. `SORTIE/inspection/` contient l'image et `page.alto.xml` ;
`SORTIE/livraison.json` donne leurs chemins et empreintes ainsi que le nombre
de lignes exportées. Un ALTO partiel reste explicitement partiel. Pour reprendre
une lecture déjà journalisée, ajouter `--transcription-dir DOSSIER_LECTURE`.
Les références d'évaluation ne doivent pas entrer dans la chaîne de production.
Pour joindre le CER normalisé HIPE-OCRepair (ICDAR 2026), ajouter
`--evaluation-manifest runs/production-20261006/suite/evaluation.json`.
Le calcul s'exécute après la production dans un processus distinct ; les
références ne sont jamais transmises à Gemini ni à l'aligneur. Le rapport
`inspection/cer-hipe.json` accompagne alors la paire image–ALTO. Sans référence
indépendante, le CER reste indisponible et n'est jamais supposé nul.

Essai presse par régions (7 octobre) : `scripts/transcrire_regions.py IMAGE
PLAN_JSON SORTIE --pane ID_VERIFIE` lit un plan de rectangles en pixels source
(`regions`: `id`, `bbox` xyxy, `order`). Le plan peut partir d'une proposition
Gemini, mais ses coordonnées doivent être vérifiées sur les pixels. Les
colonnes hautes sont accompagnées de vues de 2800 pixels avec recouvrement ;
chaque réponse native est journalisée séparément. L'assemblage garde les textes
verbatim et leurs offsets. Une interruption fournisseur reste une sortie
partielle, jamais une transcription complète.

L'essai reproductible et son plan sont dans
`runs/reprise-20261007/fronde-regions/`. Le CER global se calcule avec
`scripts/evaluer_ocr_page.py` comme pour la page entière. En complément,
`scripts/evaluer_regions.py MANIFESTE_EVALUATION SORTIE --baseline ANCIENNE_SORTIE`
diagnostique les régions et compare les deux transcriptions avec un même ordre
spatial de référence (rangées des tableaux incluses), sans corriger ni retirer
les mots de référence. Ce diagnostic ne remplace pas le score global initial.
Le protocole change à la fois les vues et la consigne de transcription : il ne
mesure pas isolément l'effet de la résolution. Les références restent hors
des appels Gemini et du placement.

Lecture seule, au prompt minimal :
`/Users/marcel/cinoc/.venv/bin/python scripts/transcrire_page.py IMAGE SORTIE --gemini-pane ID_VERIFIE --minimal-markdown`.
Gemini reçoit la seule demande « Je veux l’OCR complet de cette page en Markdown. »
et le chemin de l’image. BBVLM identifie et conserve la réponse hors du prompt.
La suite et la mesure indépendante restent celles du protocole ; aucun succès
de production n’est encore certifié.

Le candidat v3 livre la VT de page entière par portions Markdown durables :
`/Users/marcel/cinoc/.venv/bin/python scripts/transcrire_page.py IMAGE SORTIE --gemini-pane ID_VERIFIE --paged-markdown`.
Le marqueur de fin est une déclaration du lecteur ; la couverture et le CER
restent mesurés indépendamment. Les essais v2 et leurs omissions sont conservés.

# VT de page entière et coordination actuelle

La VT Gemini est maintenant sauvegardée dans `vt.gemini.md` avant toute
segmentation, géométrie ou OLR. Les refus d'ALTO ne retirent aucun texte de
cet artefact. Le candidat actif produit du Markdown naturel, avec la page
entière et des vues de détail à résolution source :

```sh
/Users/marcel/cinoc/.venv/bin/python scripts/transcrire_page.py IMAGE SORTIE --gemini-pane ID_VERIFIE --native-markdown --tile-size 1536
```

Pour la suite fixe, utiliser `scripts/transcrire_suite_pages.py` avec son
manifeste **production**, `--split dev` ou `reserved`. Le même appel reprend
les jobs identifiés et les caches ; un timeout seul n'autorise aucun renvoi.
Les réponses longues sont récupérées dans l'historique natif agy 1.2.17,
lecture seule, prompt/UUID exacts, après fin native ; aucun fichier n'est
écrit par Gemini. Les références sont chargées uniquement par
`scripts/evaluer_vt_pages.py`, avec le manifeste **évaluation** indépendant.
Voir [PROTOCOLE-VT-PAGE.md](PROTOCOLE-VT-PAGE.md) pour strict/v1/v2 et les
limites des références. Ce candidat et la chaîne ALTO/OLR restent en échec
sur les critères de production ; aucun certificat de perfection.

La propriété des fichiers, le canal Gemini exclusif et les sessions Codex /
Astra sont fixés dans [COORDINATION.md](COORDINATION.md). Le checkpoint
courant est en tête de REPRISE.txt et dans CONTINUATION.json cycle16.

# BBVLM — Produire de la vérité terrain ALTO

**État actuel (6 octobre 2026).** La chaîne est en cours de validation, avec un
objectif persistant actif. Le [protocole v1](PROTOCOLE.md) fixe la transcription,
les seuils et une suite locale de 21 pages (5 développement, 16 réservées).
Les anciennes mesures ci-dessous sont historiques : l'ancien banc pouvait
lancer Churro sous une étiquette `opus` et son juge de frontières pouvait
créditer des mots superposés. Elles ne certifient ni Gemini ni la chaîne entière.

Le pilote de 12 lignes fournies par PAGE donne 5 différences sur 474 caractères
(CER strict NFC 1,05485 %), dont deux ponctuations incertaines. Sur une première
page entière de L'Œuvre, la segmentation BLLA globale apparie 14/363 lignes à
IoU 0,50 ; les tuiles en apparient 350/363. Il reste 13 omissions et 252 sorties
sans correspondance. Aucun critère de fin n'est acquis. Les corpus/références
et sorties se trouvent sous `runs/`, hors Git.

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
- **Toute vérité terrain est vérifiée avant de servir de règle.** Le diagnostic
  historique BNL comparait des coordonnées `mm10` à des pixels ; ses mesures
  d'encre dans les blancs et son exclusion ne sont donc pas probantes. La suite
  fixe conserve les pages BNL et emploie la conversion documentée des unités
  ([COORDONNEES-EVALUATION.md](COORDONNEES-EVALUATION.md)).
- La notation porte une **distribution** — p90, p99, pire cas — jamais une
  moyenne seule.
- `JOURNAL.md` consigne chaque itération, **les échecs compris**.

## Utilisation

### Lecture Gemini et placement automatique

`src/produire.py` accepte un lecteur Gemini dans un terminal Herdr déjà ouvert.
Le lecteur reçoit des planches de lignes isolées à leur résolution d'origine,
et rend du JSON identifié par ligne. Les comptes incohérents déclenchent de
vraies sous-requêtes ; les lectures incertaines sont reprises individuellement.
Une approbation ou un problème de transport interrompt le relais et conserve
les fichiers de requête. Une relance de la même commande réutilise les réponses
validées et récupère les requêtes déjà soumises ; elle ne les resoumet pas.

```bash
python src/produire.py image.jpg sortie/ \
  --lecteur gemini --gemini-pane ID_DU_TERMINAL \
  --boxer forcectc --ctc-model modele.mlmodel
```

Utiliser un environnement avec Pillow, NumPy, OpenCV, lxml, PyTorch et Kraken.
Le placement forcé impose la transcription au CTC, conserve les accents
encodables et tient compte des marges du réseau lors du retour aux pixels.
Un caractère hors alphabet entraîne un échec explicite, jamais sa suppression.
Si CATMuS ne peut encoder la ligne (notamment `ſ`), le modèle local
`german_print` est essayé avec le même texte intact. Le modèle réellement
utilisé est enregistré par ligne. Un manque d'alphabet n'entraîne plus une
relecture qui modifierait la graphie pour satisfaire le modèle.

Les sorties comprennent `page.alto.xml`, `overlay.jpg`, `provenance.json` et
`annotations.json`. Ce dernier conserve toutes les lignes et leur statut, y
compris celles exclues de l'ALTO après les reprises automatiques. Les sorties
sont des pseudo-annotations : aucun CER nul n'est certifié. Les boîtes de mots
superposées ou hors image sont exclues, y compris entre deux lignes. L'ALTO est
validé contre le XSD 4.4 local et les références/rectangles sont contrôlés.
Les scores d'alignement restent des
diagnostics ; ils ne prouvent pas l'exactitude du texte.

Cette première commande produit un bloc temporaire par ligne. La passe OLR
suivante regroupe et type les lignes par IDs, ordonne les blocs et associe les
articles. Elle n'a aucune entrée de référence et ne fournit pas de coordonnées.
Les rectangles des blocs viennent des lignes détectées ; les groupes couvrant
des colonnes disjointes sont scindés en gardant les IDs d'articles. Sur une
nouvelle sortie, la commande active aussi PP-DocLayoutV3 local et la détection
de traits dans l'encre. Gemini accepte/type ou rejette explicitement chaque
candidat non textuel par ID. L'exactitude de ces candidats reste à mesurer.

```bash
python src/pipeline.py image.jpg sortie/ --gemini-pane ID_DU_TERMINAL
```

Le détecteur utilise par défaut `~/outils-seg/layout-env/bin/python`, avec
les poids déjà en cache local ; `--layout-python` change cet environnement.
`--layout none` permet un diagnostic textuel. Les anciennes sorties gardent
leur configuration et leur périmètre lors de la reprise.

La commande unique reprend les étapes déjà sauvegardées. Elle produit les
exports puis indique `exported_pending_independent_evaluation` ; ce statut ne
signifie pas que les critères de VT sont atteints.

Les placements CTC terminés sont désormais sauvegardés par ligne, avec les
empreintes de l'image, des recadrages, des lectures, des modèles et du code.
La reprise recalcule les collisions entre lignes et le seuil du document.
Un placement interrompu reste absent du cache. Le relais annule aussi une
demande native Bash qui sort du périmètre de lecture établi, conserve la
preuve d'annulation et reprend une fois le même UUID. Une UI inconnue ou un
timeout reste une requête à récupérer, sans renvoi ambigu. L'OLR permet une
seule réparation du contrat après un retour natif identifié et terminé.

Les étapes peuvent aussi être exécutées séparément :

```bash
python src/olr.py image.jpg sortie/ --gemini-pane ID_DU_TERMINAL
python src/export_training.py image.jpg sortie/
```

L'export produit `training.alto.xml` (TextBlock plats, tags de type/article,
ordre par IDs), `training.page.xml`, `axel-ir.json`, `training.jsonl` (mots,
offsets texte et positions CTC sur le texte NFC original), et la liste explicite
des exclusions. Il conserve le taux de couverture et le statut de
pseudo-annotation. PAGE et ALTO sont validés contre leurs schémas locaux.
Les caractères impossibles à encoder restent des échecs explicites.
Les illustrations sont exportées en ALTO Illustration / PAGE ImageRegion,
les séparateurs en GraphicalElement / SeparatorRegion, avec l'ordre par IDs.

```bash
python scripts/figer_suite.py runs/production-20261006/suite
python src/evaluation.py reference.xml sortie/annotations.json scores.json
python -m pytest -q tests
```

`evaluation.py` est réservé à la notation. Ne jamais donner le manifeste
`evaluation.json`, ses références ou ses scores à une étape de production.
`production.json` ne contient que les images et leurs empreintes.
`--segmentation tiles` permet de comparer le BLLA par tuiles ; cette option
n'est pas encore un réglage validé pour tous les corpus.
La commande entière utilise `auto` par défaut : elle choisit la résolution à
partir des composantes d'encre et journalise sa décision. Une sortie existante
créée en `full` doit être reprise avec `--segmentation full`. Le compte-rendu
mesuré et les limites sont dans [RAPPORT-PRODUCTION.md](RAPPORT-PRODUCTION.md).

`--line-refinement ink` compare une enveloppe d'encre plus précise, en gardant
le recadrage initial pour la lecture et le CTC. Cette variante est expérimentale.
Pour mesurer la segmentation sans mélanger les erreurs de lecture :

```bash
python scripts/segmenter_suite.py runs/production-20261006/suite/production.json \
  runs/production-20261006/dev-segmentation --split dev
python scripts/mesurer_segmentation.py runs/production-20261006/suite/evaluation.json \
  runs/production-20261006/dev-segmentation rapport-segmentation.json --split dev
```

Les métriques finales lisent les IDs réellement exportés et l'ordre OLR.
Un refus sémantique compte aussi comme omission, même si la géométrie de la
ligne avait réussi. Les lectures conditionnelles restent des diagnostics.

Pour vérifier le placement sans refaire une lecture, utiliser `--lecteur json
--transcription-json reponse.json`. Une segmentation externe peut être fournie
avec `--lignes-json lignes.json` (liste d'objets `id`, `bbox` en pixels, rectangles
à fin exclusive). Les boîtes de mots de référence ne sont jamais des entrées.

### Banc géométrique

```bash
python src/evaluation.py reference.xml sortie/annotations.json scores.json
```

Un boxer reçoit l'image, le **texte** de la ligne et la **boîte de ligne**.
Jamais les boîtes de mots de la vérité terrain — celles-ci ne servent qu'à noter.
Les anciennes commandes `run.py`/`run_kraken.py` injectaient le texte de
référence. Le juge refuse maintenant ce mode sans lectures de production
séparées ; les anciens chiffres restent des diagnostics oracle historiques.

## Reprise de session

L'état du travail automatique Gemini/CTC est dans `CONTINUATION.json`.
`REPRISE.txt` contient le prompt à donner à une nouvelle session. Les résultats,
recadrages et scripts du pilote sont sauvegardés localement sous
`runs/gemini-pilot-20261006/`, hors Git, avec un manifeste SHA-256.

## Licence

Apache-2.0.

### Pages denses et contrôle des données d’entraînement

Les nouvelles sorties utilisent un réalignement forcé au mot pour les
positions des caractères. Les espaces sont des intervalles blancs observés
avec confiance CTC inconnue (= 0), identifiés par `character_position_sources`.
`--char-alignment line` conserve le diagnostic de treillis de ligne.
Les anciens dossiers gardent leur configuration. `--word-boundaries ink`
exige une vraie colonne blanche entre les pics adjacents ; les variantes
`ink_clean`, `ink_clean_baseline`, `ink_clean_local` sont expérimentales.
Les 12 lignes PAGE du diagnostic ne valident pas la page entière.

Une nouvelle sortie active `--word-verification blind` : seuls les refus
du coût de police peuvent être vérifiés par TOUS leurs mots natifs. Les mots
attendus restent dans BBVLM et ne sont jamais transmis à Gemini. Un
désaccord ou une incertitude garde le refus. Les anciennes sorties conservent
`none`. Cette passe attend encore son essai natif indépendant.

L’OLR des pages de plus de 128 lignes travaille sur des groupes géométriques
et des fichiers compacts : tous les IDs de lignes restent couverts exactement
une fois. Les groupes ne sont pas des articles de référence. L’expansion des
segments par IDs est contrôlée avant export.

Les IDs de page IR/JSONL dérivent du SHA de l’image, pour éviter les collisions
lors de l’assemblage du corpus. Le modèle déclaré par Gemini et le modèle
affiché par son terminal sont conservés séparément, avec les UUID de lecture.
Vérifier les lecteurs réels, dans l’environnement Kraken :

```sh
python scripts/verifier_lecteurs.py sortie/ --axel-root /Users/marcel/axel
```

Cette commande vérifie textes, IDs, ordre, NFC, offsets des mots, positions,
image et l’aller-retour intégral de l’IR. Elle ne certifie pas la qualité OCR.


### Checkpoint autonome du cycle 7

70 tests passent. La Fronde entière produit 451 lignes exportables sur 1007,
avec un ALTO valide et des lecteurs Kraken/Axel exacts, mais un CER exporté de
62,02 % refus inclus. L'OLR native est complète au sens des IDs, avec un article
unique : qualité sémantique encore non démontrée. La réparation de capture
emploie un format compact puis, si un JSON identifié complet est encore invalide,
un seul tour de contrat supplémentaire ; les preuves et retours bruts restent
sauvegardés. Une livraison ambiguë n'est jamais renvoyée.

OCR17 atteint 19/19 lignes après vérification aveugle des mots de la ligne
refusée ; CER conventionnel 1,02 %, strict 3,27 %, sans perfection. Les 16 pages
réservées sont segmentées et mesurées, mais leur chaîne VT/ALTO/OLR reste à
produire. Les masques polygonaux expérimentaux et les audits de rectangles/encre
ne modifient aucun seuil ni refus. Voir RAPPORT-PRODUCTION.md et
CONTINUATION.json production_cycle_7 pour les mesures et la reprise du job OLR AS.


### Checkpoint du cycle 8

76tests passent. Les unités ALTO physiques exigent un DPI documenté dans
l'évaluation (`--reference-dpi 300` pour BNL) ; les anciens scores BNL non
convertis sont invalides. Voir COORDONNEES-EVALUATION.md. La stratégie explicite
`--segmentation auto-v2` améliore les petits canevas sur les21pages fixes sans
régression mesurée, avec refus et couverture conservés. `--segmentation-from`
réutilise uniquement les segmentations automatiques de mêmeimage/configuration.

Le diagnostic natif AS OLR échoue : tous232blocs incertains, aucunarticle résolu,
F1détection0,772, F1articles primaire0. Un ensemble vide ne reçoit plusF1=1.
Le driver des4devrestants est actif ; Gemini lui est réservé. Les preuves,
commandes et requêtes à récupérer sont dans CONTINUATION.json production_cycle_8.
La fidélité des glyphes et l'OLR demeurent à améliorer : aucune perfection acquise.


### Checkpoint du cycle 9

78 tests passent. Le rejeu expérimental `scripts/reparer_positions.py` corrige
deux intervalles nuls de virgules à partir de l’encre native, garde les anciens
pics CTC et déclare une confiance inconnue. Son export isolé conserve19/19 lignes,
valide PAGE/ALTO et passe Kraken/Axel ; CER conventionnel1,02%, strict3,27%.
La fidélité des glyphes n’est pas certifiée et la variante n’est pas promue.
Le driver est interrompu par une erreur réseau native ; une reprise identifiée
est en cours. Voir CONTINUATION.json production_cycle_9 avant toute requête.


### Checkpoint du cycle 10

83 tests passent. La reprise réseau a effectivement récupéré les huit lignes
identifiées ; le driver dev reprend depuis ses caches. La nouvelle voie OLR
locale conserve les pixels natifs et prépare des lots sans omissions, puis une
réconciliation globale obligatoire des articles et de l’ordre. Son essai natif
reste à effectuer ; l’ancien diagnostic OLR en échec reste dans le verdict.

```sh
python scripts/diagnostiquer_olr.py production.json PAGE_ID \
  segmentation-automatique.json candidats-layout.json sortie/ \
  --gemini-pane ID_DU_TERMINAL --mode local --local-batch-groups 8
```

`--prepare-only` prépare les vues sans utiliser Gemini. La commande est un
diagnostic OLR seul : elle ne produit aucune VT ni certification d’entraînement.
Ne lancer qu’un utilisateur du terminal Gemini à la fois ; reprendre le même
dossier récupère les jobs existants, sans renvoi aveugle après timeout.


### Checkpoint du cycle 11

88 tests passent. Deux fragments physiques sont identifiés expérimentalement
par texte Gemini, ancres CTC et encre commune ; leur encre est conservée dans les
mots canoniques. La couverture exportée reste inchangée : la variante n’est pas
promue. L’essai d’échelle sur les21pages est en cours, avec tuiles recouvrantes,
cache de reprise et canevas réseau borné. Pour le reproduire par split :

```sh
python scripts/segmenter_echelle.py production.json sortie/ \
  --split dev --routing bounded
```

### Checkpoint du cycle 12

98 tests passent. Le Matin conserve1200lectures validées ; le diagnostic de
lecture seule donne7,58% de CER conventionnel et8,25% strict, refus et sorties
supplémentaires inclus. L’ALTO/OLR final reste requis. Le quota natif a empêché
69relectures : les placements intermédiaires concernés sont en quarantaine
réversible, les lectures et preuves originales restent intactes.

`scripts/produire_suite.py --wait-native-quota` attend l’échéance explicitement
affichée par Gemini, sauvegarde cet état et récupère la même requête avec preuve
de fin native. La garde partagée du terminal arrête aussi les demandes de format
et OLR pendant le quota. Un timeout seul ne déclenche aucune resoumission.
L’attente réelle est vérifiée ; la reprise native après remise à zéro est encore
à démontrer. Voir CONTINUATION.json production_cycle_12 pour la commande active.

Les essais d’échelle et de complément conservateur ont des régressions sur les
cinq pages dev ; ils restent expérimentaux et non promus. L’essai d’échelle
continue sur les seize pages réservées. L’objectif persistant reste actif.

### Checkpoint du cycle 13

109 tests passent. `scripts/reparer_mots_terminaux.py` est un essai isolé qui
observe les composantes natives entières dans un recadrage plus large que le
mot proposé. Il conserve les anciens rectangles/positions et une confiance
de position inconnue. Une fausse attribution au point d’une ligne voisine et
un point tronqué par le bord du mot ont été réfutés visuellement puis corrigés.

Le Matin partiel passe de17 à4intervalles non blancs nuls, avec9IoU de mots
améliorés et1régressé sur10comparables, mais sans gain de couverture : les
collisions dominent encore. L’export OCR17 isolé conserve19/19 et488positions,
valide PAGE/ALTO et passe les vrais lecteurs Kraken/Axel ; CER inchangé1,02%
conventionnel/3,27%strict. Ces variantes ne sont pas promues ni certifiées.

```sh
python scripts/reparer_mots_terminaux.py image annotations.json essai.json \
  --hyphen-min-aspect 1.4
```

Le driver principal attend le reset explicite du quota ; les travaux locaux et
la comparaison d’échelle continuent. Voir CONTINUATION.json production_cycle_13.

La notation indépendante, toutes pages et omissions incluses, reste obligatoire
avant promotion. Les critères gelés et les échecs précédents sont conservés.
Le traitement Matin reprend ses lectures en cache ; les UUID actifs sont dans
CONTINUATION.json production_cycle_11. Aucun fichier Axel n’est modifié.

### Checkpoint du cycle 14

120 tests passent. Les essais d’encre depuis les baselines automatiques sont
isolés dans `scripts/rejouer_encre_baselines.py`. L’attribution complète des
composantes régresse. Le filtre conservateur ne retire une composante locale
entière que si au moins95%de ses pixels sont attribués à un seul autre ID.
Les ponctuations près de leur baseline et les traits horizontaux sont conservés.
La Fronde passe de451 à521lignes retenues, mais la couverture n’atteint que
47,09%des caractères ; les critères restent non atteints. Les caractères CTC
historiques sont inchangés et ne constituent pas une certification des glyphes.

```sh
python scripts/rejouer_encre_baselines.py image dossier-production essai
python scripts/diagnostiquer_encre_baselines.py production.json segmentation essai \
  --split dev --source-geometry ink
```

La géométrie de lignes est mesurée sur les cinqdev : gain àIoU0,75 surMatin,
Presse etŒuvre, régressionFronde, OCR17inchangé. Tous16réservés sont en cours.
Le driver Gemini a réellement repris après le quota avec les mêmesUUID et
sauvegarde ses réponses. Voir `CONTINUATION.json` production_cycle_14.

### Checkpoint du cycle 15

127 tests passent. Le relais conserve le fournisseur déclaré et peut normaliser
le libellé Google en gemini seulement sur preuve native : modèle Gemini, UUID
exact et footer Gemini suivant cette réponse, sans nouvelle requête ultérieure.
Le texte et le modèle déclaré restent inchangés. Une erreur de fournisseur
interrompt le traitement avec sa preuve ; elle ne devient plus un refus OCR vide.
Le cas natif L0044 est réparé depuis la capture sauvegardée sans nouvel appel.

Le worker est rechargé après nativeDone et sauvegarde de sa requête en cours
par get/read, sans renvoi. Le nouveau driver reprend les caches. Les16réservés
du diagnostic d’encre sont tous mesurés : gains partiels et régressions conservées,
variante non promue. La chaîne complète reste non certifiée et le goal actif.
Voir `CONTINUATION.json` production_cycle_15.

### OCR de presse par régions, reprise du 7 octobre 2026

Le point d'entrée `scripts/ocr_presse.py` calcule les colonnes et les filets
depuis les pixels et la segmentation BLLA, puis fait lire chaque région par
Gemini. Les grands titres traversants et les cadres publicitaires sont traités
séparément. La sortie Gemini reste immuable : le CTC sert à la localiser et à
placer les mots. Le contrôle des pixels conserve les parties exploitables
d'une ligne quand quelques mots restent ambigus.

```sh
/Users/marcel/cinoc/.venv/bin/python scripts/ocr_presse.py \
  image.jpg auto dossier-sortie --gemini-pane w6:p5
```

Le pane doit être celui de Gemini dans la session Herdr courante ; vérifier
son identité avant l'appel. Remplacer `auto` par un dossier contenant une
segmentation automatique permet de réutiliser ce calcul. L'option
`--evaluation-manifest chemin/evaluation.json` calcule le CER **après** la
production, dans un processus séparé. Les références ne sont jamais envoyées
à Gemini ni utilisées par le placement.

Relancer la même commande reprend les réponses et placements journalisés.
Le plan déjà sauvegardé reste figé. Après `/clear`, le relais attend une
nouvelle conversation native vide avant de soumettre le prompt. Une réponse
interrompue reste signalée ; elle n'est pas présentée comme une lecture complète.

`livraison.json` donne les chemins et empreintes de l'image originale, de
`inspection/page.alto.xml` (ou la sortie affinée dans `inspection-refined`), du
Markdown et des audits. Le CER conserve
distinctement l'ordre XML original et l'ordre spatial commun aux régions :
un changement d'ordre de lecture peut fortement gonfler le premier. Le calcul
HIPE conserve ses règles officielles, notamment pour les espaces et césures.

Les chevauchements de rectangles ALTO ne sont acceptés que pour les paires
explicitement auditées sans pixel d'encre attribué commun. L'autorisation est
liée aux empreintes de l'image et des annotations ; le validateur reste strict
par défaut. Cela ne certifie ni la lecture ni chaque glyphe. Les régions dont
le découpage reste ambigu, les mots non placés et les réponses interrompues
restent dans les rapports. État de la boucle en cours :
`runs/industrialisation-20261007/reprise.json`.

Quand le fond gris bouche les espaces entre mots, une seconde passe reprend
uniquement les frontières CTC refusées. Le seuil de contraste Otsu et les
baselines voisines retirent l'encre parasite sans ajouter de pixels sombres.
Les placements initiaux et les essais refusés restent conservés. La géométrie
de caractères est auditée séparément des mots : un ALTO de mots exploitable
ne constitue pas une certification des positions de chaque caractère.

Pour copier les résultats dans un dossier d'inspection :

```sh
python scripts/livrer_ocr_presse.py dossier-sortie dossier-inspecteur \
  --inspection dossier-sortie/inspection-refined
```

Cette livraison vérifie les empreintes, le schéma ALTO, les permissions de
chevauchement et les preuves natives de lecture. Les vues de détail peuvent
couvrir tous les pixels même si Gemini n'a pas ouvert la vue d'ensemble.
Les réponses vides identifiées restent signalées comme telles, sans nouvel
envoi aveugle. Une référence qui omet des régions entières est signalée ; le
score conditionnel sur les régions couvertes est distinct du CER de page.
