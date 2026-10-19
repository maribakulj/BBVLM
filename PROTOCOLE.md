# Protocole de production et d'évaluation v1 — 6 octobre 2026

Ce protocole est fixé avant les nouveaux essais. L'objectif est une production
automatique de VT Gemini, d'ALTO au mot et d'OLR, sans validation humaine. Les
références humaines préexistantes sont des instruments de notation indépendants.
Une réussite sur cette suite ne constitue pas une perfection universelle.

## Séparation des données

`scripts/figer_suite.py` fige les chemins et SHA-256 des images et références.
Le manifeste **production** ne contient que les images et leurs empreintes ;
le manifeste **évaluation**, local et hors Git, contient les références. Aucun
module de production ne doit importer le chargeur de références. Gemini et
l'aligneur ne reçoivent ni texte, ni lignes, ni régions, ni mots de référence.
Les diagnostics sur lignes PAGE restent identifiés comme diagnostics.

La suite de développement comprend les trois pages du pilote, la première
page OCR17 par chemin trié et la première page de L'Œuvre. La suite réservée
comprend deux autres pages par titre La Fronde, Le Matin, La Presse et L'Œuvre,
deux autres pages OCR17, deux pages BNL par chemin trié, puis deux pages AS par
titre dans le split test Axel, séparées par numéro. La sélection précède les
mesures, ne dépend ni du CER ni de la qualité géométrique. Les pages entières
sont traitées, sans limite de lignes. Un fichier manquant est un échec de la
suite, jamais une exclusion silencieuse. Une page réservée devient une page
d'épreuve connue dès sa première mesure ; les itérations répétées sur elle ne
doivent plus être qualifiées d'évaluation aveugle.

## Transcription diplomatique et conventions

Copier casse, accents, graphies anciennes, ponctuation, ligatures et césures
imprimées. Ne pas moderniser, compléter ou corriger la langue. Conserver le
texte original NFC, les incertitudes et toutes les tentatives dans les sorties.

Le CER strict est la distance de Levenshtein sur les caractères Unicode NFC.
Pour une ligne PAGE, prendre TextEquiv/Unicode direct ; à défaut joindre les
Word/Unicode par une espace. Les espaces de bord de l'annotation sont ôtées.
Les retours entre lignes sont mesurés séparément dans le CER de page ordonnée.

Le CER de convention applique **uniquement**, avant la distance : NFC,
apostrophe courbe U+2019 vers U+0027, espaces Unicode vers U+0020 (suites
réduites à une espace), marqueurs de césure U+00AC et U+2E17 vers tiret U+002D
uniquement en fin de ligne. Aucune équivalence virgule/point, deux-points/
point-virgule, s long/s, accent, casse ou ligature. Ces règles ne modifient
jamais les transcriptions de production.

## Mesures indépendantes

- Lecture : CER strict et de convention, erreurs absolues et lignes exactes,
  sur toutes les références. Appariement géométrique un-à-un, sans texte, à
  IoU ≥ 0,50. Ligne absente : toutes ses lettres comptent comme suppressions ;
  ligne prédite sans correspondance : son texte compte comme insertions.
  Le CER conditionnel des lignes appariées est fourni en diagnostic.
- Segmentation : précision, rappel, F1 à IoU 0,50 et 0,75 ; lignes fusionnées,
  omissions, faux positifs et couverture pondérée par caractères. Les refus
  sont comptés même lorsque leur transcription est conservée pour diagnostic.
- Géométrie des mots : correspondances lexicales exactes dans une ligne
  appariée ; couverture rapportée sur **tous** les mots de référence. IoU
  p10/médiane, erreurs des quatre bords en pixels et largeurs de caractères,
  p90, p99 et maximum. Frontière interne : noter séparément le bord droit du
  mot gauche et le bord gauche du mot droit, pas leur milieu. Toute
  superposition ou boîte hors image échoue au contrôle, quel que soit le score.
  Références géométriques imparfaites : conserver la page pour le texte et
  signaler séparément les anomalies, sans les retirer après mesure.
- OLR AS : détection non typée, classification typée, ordre des lignes et
  blocs, regroupement des articles, couverture et refus sont séparés. Les
  annotations textuelles AS non humaines ne certifient pas le CER. Les types
  génériques `paragraph` des PAGE ATR ne certifient pas les titres/annonces.

## Critères de fin

Sur **chaque** famille de la suite entière : CER de convention = 0, toutes
les lignes de référence couvertes, aucun refus, aucun texte inventé ; CER
strict publié avec ses différences de convention. ALTO validé contre le XSD
4.4, texte fidèle, IDs uniques/références valides, mots contenus dans la page
et la ligne, zéro chevauchement entre mots et zéro placement synthétique.

Le critère géométrique historique de CRITERE.md demeure : ≥ 95 % des
frontières à ≤ 0,5 caractère, maximum ≤ 3 caractères, IoU médian ≥ 0,80,
aucune ligne en échec, aucune régression du pire cas contre proportionnel.
Le contrôle des deux bords et des superpositions s'y ajoute. Les quatre bords
doivent avoir p99 ≤ 1 caractère et maximum ≤ 3 caractères ; couverture des
mots = 100 %. Les anomalies des références restent explicitement non résolues.

OLR : F1 de détection à IoU 0,50 ≥ 0,95, exactitude des types appariés ≥ 0,98,
Kendall des lignes = 1, F1 pairwise des articles = 1, couverture = 100 % sur
chaque titre AS. Les métriques Axel supplémentaires restent publiées. Les
séparateurs et illustrations ont leurs scores et ne sont pas cachés.

Une commande doit reprendre une interruption en conservant les requêtes
identifiées et caches ; jamais de resoumission ambiguë après timeout. L'export
doit être lu par Kraken PAGE/ALTO et par l'IR Axel ; NFC et une position par
caractère lorsqu'elles sont exposées doivent être vérifiés. Tous les résultats,
échecs, configurations, versions et empreintes doivent être sauvegardés.
L'objectif persistant reste actif tant qu'un seul de ces critères manque.
