# Implémentation locale — état vérifiable

Base : `maribakulj/BBVLM@60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`.
Copie des 61 fichiers textuels obtenue via l'API GitHub authentifiée ; le clone
HTTPS privé était indisponible. Le commit initial local représente cet instantané,
pas l'historique Git original. Fonte et anciens overlays binaires non récupérés.
Aucun changement envoyé à GitHub.

## Disponible et exécuté ici

- Graphe JSON avec pages, régions, lignes, mots, polygones, baselines, unités
  sémantiques distinctes des articles,
  ordre de lecture, métadonnées sourcées, propositions et journal de modifications.
- Import ALTO et PAGE, sans supprimer les lignes d'un seul mot. XML source conservé
  pour les éléments hors profil ; l'export est une projection normalisée, pas un
  convertisseur universel sans perte.
- Coordonnées internes xyxy semi-ouvertes. Adaptateur explicite pour les anciens
  boxers à bornes d'encre inclusives.
- Application atomique des réponses par identifiant, contrôlée contre un lot
  demandé indépendamment. Un texte changé invalide ses anciennes boîtes ; les
  anciennes valeurs restent au journal. Aucune validation humaine automatique.
- Export ALTO 4.4 avec tags de statut/rôle et géométrie conservée ; ordre explicite
  exporté seulement si le graphe détermine un ordre total unique des régions de
  la page. Les ordres partiels restent dans le graphe.
- METS 1.12.1 : cartes physique/logique et liens article → régions ALTO. Champs
  sourcés dans un bloc de métadonnées BBVLM explicite. Pas de prétention de
  conformité à un profil institutionnel BnF, MODS ou PREMIS.
- Les attributs enrichis non normatifs `SSU_ID`, `BLOCK_TYPE` et
  `READING_ORDER` peuvent être importés comme preuves automatiques. Les SSU
  deviennent des divisions logiques METS `semantic-unit`, jamais des articles
  par simple renommage. Les exports ALTO restent conformes au XSD standard.
- Validation hors ligne avec ALTO, METS et le XLink compatible, sans modifier
  les XSD. Vérification des références et cycles du graphe.
- Préparation de crops et consigne VLM, modes lecture aveugle ou correction OCR.
- Mesures CER stricte/normalisée et appariement exact texte + IoU au mot, avec
  les sorties manquantes conservées dans les dénominateurs.
- Pilote réellement lu par Terra/Luna, puis une reprise ciblée chacun.
- Tests de non-régression sur les quatre ALTO déjà présents dans le dépôt et
  sur la page ONB complète ; tests de comportements négatifs et de production
  avec entrées contrôlées.

## Production existante

`src/produire.py` délègue au nouveau pont `bbvlm.production`. Les baselines,
polygones et régions Kraken sont conservés. Sans appartenance de région connue,
une ligne reçoit un bloc non classé distinct ; aucun article n'est inventé.
Les lignes rejetées ou hors `max_lignes` restent dans le graphe et dans l'export.

Le lecteur historique renvoyant une liste positionnelle est limité à une ligne
par appel. Pour les lots, le lecteur doit exposer `returns_ids=True`, recevoir
la liste d'identifiants et retourner `({id: texte}, qualité)`. Les lots ne
traversent pas les régions. L'interface générique `prepare` donne des crops
individuels explicitement nommés pour éviter de confondre position et identité.

Le seuil automatique d'ancien coût d'encre n'est plus un motif de suppression
des lignes. Le nouveau pont vérifie comptes et géométrie ; toutes les lectures
restent à valider. Un routeur d'erreur calibré et les contrôles visuels d'encre
restent à intégrer/évaluer, sans quota de corrections imposé.

## Adaptateur PERO : exécuté sur CPU avec un modèle réel

`bbvlm.pero.save_cache(layout, dossier, model_id)` conserve PAGE, logits NPZ et
alphabet/indices JSON après une reconnaissance PERO. Le chargement vérifie les
empreintes de géométrie et de logits. Aucun pickle externe à désérialiser.

`python -m bbvlm pero-realign CACHE TEXTES.json sortie.alto.xml` réutilise ces
sorties et appelle l'alignement/export natif PERO. Les caractères inconnus sont
refusés au lieu d'être substitués. Les signaux de confiance nulle/repli sont
signalés pour relecture. L'ALTO natif peut ensuite être importé dans le graphe.

PERO 0.7.0, torch 2.14 CPU et les poids publics eu/cz newspapers du 26/09/2022
sont maintenant installés. Les 2 336 lignes des trois pages françaises NewsEye
avec boîtes de mots ont été reconnues et mises en cache. L'alignement natif et
sa reprise depuis le cache ont été exécutés. Les protocoles, scores et empreintes
sont dans `experiments/loop/`. Aucun GPU ni clé d'API n'est utilisé : les lectures
VLM réelles passent ici par les sous-agents autorisés.

## Boucle expérimentale et recherche

`scripts/autonomous_loop.py --execute` reprend les phases CPU manquantes et
écrit `experiments/loop/CHECKPOINT.json`. La lecture de littérature, les nouvelles
hypothèses et les appels VLM sont réalisés par l'agent autour de ce pilote ; un
script Python seul ne remplace pas ces capacités. Une phase achevée n'est pas
relancée sans raison. Les tests consommés ne redeviennent jamais indépendants.

Le candidat G01 affine uniquement la hauteur des boîtes par composantes d'encre
bornées. Choisi parmi 12 réglages sur une page, figé avant les deux pages test,
il améliore l'IoU sur chacune. Voir le rapport pour les régressions individuelles
et les limites : lignes et textes fournis par référence dans ce premier test.

Chaque export inclut désormais `retrieval.sqlite`, référencé dans le METS.
La recherche par ligne renvoie les preuves et le texte diplomatique inchangé.
Elle ne remplace pas une recherche sémantique interlingue ni son évaluation.

Le corpus Spiritualist est restaurable par révision et SHA-256. Son audit
exhaustif refuse ses boîtes au mot ; le pilote 0009 les met en quarantaine tout
en conservant le XML source. L'image compagnon est reliée par une règle explicite
et une empreinte, car le nom JPG interne à l'ALTO ne correspond pas au PNG du
repo. Une sortie normalisée ALTO/METS conserve SSU et ordre sans blanchir les
4 525 violations XSD de la distribution.

Le transport OLR VLM possède maintenant un binder strict (`bbvlm.binding`) : le
modèle ne manipule que des jetons courts dessinés sur la page ; le programme
contrôle couverture/unicité/vocabulaire puis les remplace par les IDs stables du
graphe. Il n'existe aucun correcteur approximatif d'ID. Le test gelé A03 démontre
que cela élimine l'échec de recopie d'A02 (42/42 régions adressées, deux pages,
une passe), mais pas les erreurs de contenu : l'ordre, les rôles et surtout les
SSU restent sous les seuils. Les pages 0003/0008 sont désormais consommées et ne
peuvent servir à retuner puis à revendiquer une validation indépendante.

`bbvlm.order.infer_column_major_order` fournit désormais un chemin CPU sans
modèle pour les pages à colonnes simples. Il infère les ancres depuis les boîtes,
ordonne gauche→droite puis haut→bas et renvoie les arêtes adjacentes directement
compatibles avec le graphe. Sur la validation 0014 conditionnée aux `TextBlock`,
il obtient 378/378 paires en moins d'une milliseconde, sans texte ni passe VLM.
Les arêtes restent des propositions : le candidat brut inclut encore les régions
hors flux et nécessite un filtre de rôle validé. Cette voie rapide doit rester
derrière une détection de cas sûr ; les flux entrelacés et la
continuité d'article demeurent des tâches sémantiques avec abstention.

`bbvlm.binding.bind_semantic_page` sépare désormais ce qui reste à demander au
VLM : rôles contrôlés, sous-ensemble éligible, partition sémantique et
incertitudes. Il refuse toute perte/duplication de jeton, type de groupe hors
vocabulaire ou réparation d'ID ; aucun ordre n'est demandé. L'audit des seules
pages développement fixe la convention avant validation.

Sur 0015, Luna en une passe identifie exactement le flux utile et le chemin CPU
reproduit toutes les 171 relations d'ordre ; 20/22 rôles concordent. Le
groupement conserve un rappel élevé mais fusionne deux unités contiguës, donc le
F1 par paires reste 0,759 et le gate échoue. Cette sortie n'est ni réparée ni
promue en article.

`bbvlm.semantic.group_header_units` déplace ensuite l'assemblage hors du VLM :
ordre colonnaire gelé, nouveau titre = nouvelle unité, sauf titres multi-blocs
qui se chevauchent verticalement. Le développement atteint 1,000 avec rôles
oracle. Sur la validation 0029, la passe Luna minimale reste le goulet : 17/27
rôles, rappel du filtre 16/23 et F1 SSU 0,680. Le code protège aussi la partition
si un fragment `MASTHEAD` est déclaré éligible par erreur.

`bbvlm.binding.bind_faceted_page` impose désormais deux cartes exhaustives et
orthogonales. Le rôle physique commande le flux ; le genre éditorial est une
proposition sourcée qui ne peut supprimer de contenu. A07 confirme ce garde-fou
sur 0039 : 21/21 régions et 210/210 relations d'ordre. La distinction fine
HEADER/TEXT reste mauvaise et déplace plusieurs frontières (F1 SSU 0,591).

`scripts/calibrate_spiritualist_header_geometry.py` prépare la réduction
suivante : le VLM ne devra plus décider HEADER contre TEXT, seulement
STREAM/MASTHEAD/OTHER/UNKNOWN et le genre. Un seuil normalisé de 0,020, choisi
sur développement uniquement, sépare ensuite les blocs STREAM. Il atteint
0,969 de F1 SSU macro en développement. La validation 0044 confirme cette partie :
13/13 rôles et F1 SSU 1,000. `bind_coarse_faceted_page` et
`refine_stream_roles_by_height` appliquent le contrat sans laisser le genre
supprimer du contenu. Le gate A08 échoue néanmoins sur l'ordre (38/45), car
l'ordonnanceur fusionne deux des trois colonnes. Les tests sont maintenant 37/37.

`infer_column_major_order` accepte maintenant une largeur minimale d'ancre et
une affectation par recouvrement avec les intervalles de colonnes. A09 conserve
100 % sur développement et obtient 36/36 sur 0050. Le goulot devient un titre
multi-ligne trop haut pour la règle 0,020 ; F1 SSU 0,733.

DocLayout-YOLO 0.0.4 et son poids DocStructBench exact ont été testés sur CPU :
95,9 % de couverture d'union mais 25 régions proposées pour 13 de référence et
7/13 appariements IoU≥0,5. L'intégration doit donc rester une proposition
granulaire à fusionner/valider, pas remplacer directement PERO.

`refine_stream_roles_by_typography` corrige ensuite le défaut A09 sans ajouter
de passe : un bloc STREAM court devient HEADER si ses lignes sont assez grandes
ou majoritairement en capitales. Les trois seuils sont sélectionnés sur le
nouveau développement v6. La validation conditionnelle 0004 atteint 1,000 pour
rôle, groupement SSU et ordre ; le texte diplomatique n'est jamais réécrit par
ce classifieur. Le résultat ne couvre ni la détection de régions ni la décision
STREAM du VLM, qui sera testée séparément sur 0010.

A11 réalise ce test : une passe Luna ne fournit que les axes grossiers, puis le
CPU applique A10. Le contrat brut est valide et les seuils passent (F1 SSU
0,857, ordre 1,000). Un bloc lisible classé `OTHER` par la source est proposé
`STREAM/NOTICE`; il reste donc indexable, tandis que l'appartenance au flux
principal est conservée comme désaccord à revoir. Aucun appel Sol n'est déclenché :
Luna n'a signalé aucune incertitude et le contrat ainsi que les gates ont passé.

## Limites explicites

A14 ajoute `route_lines_to_columns` : chaque ligne prédite entière conserve son
ID, son polygone et sa baseline ; la colonne est un rattachement de contexte,
pas une découpe. Le routeur s'abstient si le recouvrement maximal est <0,8 et
signale les débordements. Les coordonnées hors image restent en preuve, avec
une fenêtre de pixels explicitement bornée. Une vraie détection PERO CPU sur
0044 (8,30 s, 2 forwards adaptatifs) fournit 416 lignes. Sur ces mêmes sorties,
l'assignation PERO aux colonnes produit 496 fragments (635 avec contexte), le
rattachement entier 416 ; les quatre variantes ont 385/418 appariements IoU≥0,5.
Le polygone brut est une prédiction : le préserver n'en certifie pas l'exactitude.

A15 relie les trois lectures Sol A13 à 20 lignes prédites A14 sans annotation
source. Une reconnaissance CTC réelle de ces 20 crops (3,32 s) puis son
alignement sur le texte VLM (1,24 s de dernier replay) produisent 184 mots.
Le cache évite toute nouvelle reconnaissance aux replays. Le paquet ALTO 4.4 /
METS passe les XSD ; les 20 lignes restent à relire. Il couvre seulement cet
échantillon, pas les 416 lignes de la page. L'index lexical contient 20 passages.

Défaut d'intégration trouvé et corrigé : PERO natif omet les IDs des TextLine et
String. `bind_native_alto_ids` restaure les liens avec contrôles des blocs, du
nombre de lignes, du texte et des dimensions entières. Tout écart fait échouer
l'export. Le graphe récupère ensuite polygones/baselines prédits, car le natif
réduit la baseline ALTO à une moyenne scalaire. Les drapeaux numpy.bool_ sont
convertis explicitement pour que le rapport de relecture soit sérialisable.
L'inspection des overlays révèle encore des tirets longs finaux hors boîte :
aucun drapeau natif de repli ne suffit à établir une géométrie parfaite.

A12 ajoute `bbvlm.columns.propose_column_windows` : ancres plain-text YOLO,
partition couvrant toute la largeur, fenêtres de contexte qui se recouvrent,
conservation de tous les IDs, titres traversants et classes non-corps à revoir.
Même `abandon` n'autorise aucune suppression. Les paramètres A09 sont réutilisés
sans recalibration sur 0044. `evaluate_yolo_columns.py` sauvegarde les propositions
avant de charger le XML d'évaluation. Aucun mot ALTO n'est inventé à ce stade.

Architecture à comparer : image → propositions/colonnes → lignes géométriques
conservées entières → transcription VLM → alignement au mot sur texte final.
L'ordre physique peut guider la lecture avant OCR ; l'ordre logique, les suites
d'articles et les notes nécessitent le contenu et des relations typées après
lecture. Toute correction de transcription invalide l'alignement précédent.
Les fenêtres de colonnes servent au contexte, pas de frontières dures coupant
les lignes. Un masque de titre traversant doit préserver un accès aux pixels.

`prepare_yolo_ocr.py` / `evaluate_yolo_ocr.py` ajoutent A13 : crops natifs issus
des seules détections, IDs hachés, réponse stricte, CER des régions avec seulement
les espaces homogénéisés. Réponses brutes et associations source conservées.
Les petites images exactes du test sont désormais incluses dans le checkpoint.

Correction de portée A10/A11 : les régions, la géométrie interne des lignes et
leur texte sont issus du corpus. Le calcul des capitales est donc oracle-text.
Ces essais ne valident pas un pipeline image seule, même lorsque Luna fournit
les rôles grossiers. Le nom historique `v6-full` ne change pas cette limite.

Pas d'entraînement ; pas de production end-to-end de VT au mot certifiée ; pas
de résolution d'autorités ; pas de profil BnF MODS/PREMIS final ; pas d'interface
d'arbitrage humain signée. La file de relecture est un JSON exploitable, pas
encore un atelier graphique. Tableaux et figures restent des régions avec rôles,
pas une reconstruction de cellules implémentée.

Le pilote VLM allemand couvre 25 lignes d’une seule page avec segmentation de référence ;
le test français utilise maintenant des lignes prédites. Aucun des deux ne suffit
à certifier une qualité générale de VLM frontier.
La prochaine étape scientifique est de distinguer explicitement contenu
recherchable et flux principal, puis de valider cette politique sur une page
encore intacte. Le genre reste non gating.
Toutes les pages du split de validation initial sont consommées. Il faudra ensuite
comparer sur les mêmes
entrées PERO natif, BBVLM et leurs variantes. La métrique principale de production
reste le temps humain par page complètement vérifiée ; ce temps n'est pas mesuré ici.

## A16 — extension additive d'encre

`extend_words_to_foreground` complète G01 sans jamais rétrécir une boîte native :
masque du polygone de ligne prédit, composantes connexes, cellules horizontales
d'appartenance et distance bornée par la hauteur de ligne. Chaque décision est
auditée. `select_edge_punctuation_extensions` fournit le routeur prudent fondé
sur la ponctuation attendue au bord du token.

Les deux premières variantes sont conservées comme résultats négatifs : A16a
modifie 179/184 boîtes et A16b 72/184. A16c ne conserve que quatre extensions de
ponctuation, dont les deux cadratins visibles, sans chevauchement voisin. Le
paquet reste entièrement en revue : ni Otsu, ni le texte du token ne prouvent
l'appartenance exacte des pixels. Texte diplomatique, IDs stables, confinement
additif et XSD sont vérifiés. La suite compte 52 tests réussis et un fixture
portable omis.

La dépendance CPU utilise `opencv-python-headless==4.8.1.78` : la roue GUI 4.10
déclenchait SIGBUS à l'import dans ce runtime AVX-512, et BBVLM n'utilise aucune
fonction HighGUI. C'est une correction d'environnement, pas un gain expérimental.

## A17 — profil METS/MODS/PREMIS et liens de fichiers

`export_package` construit maintenant ses payloads avant le METS, calcule leur
taille et SHA-256, puis écrit seulement après validation. Le METS possède quatre
groupes (`OCR`, `MASTER_IMAGE`, `DOCUMENT_GRAPH`, `RETRIEVAL_INDEX`) ; chaque
page physique pointe vers l'image et l'ALTO. `audit_mets_package` résout tous
les `DMDID`, `ADMID` et `FILEID`, vérifie les fichiers locaux et refuse une
altération. A17 vérifie aussi l'image publique restaurée contre l'empreinte A15.

Le `dmdSec` MODS 3.8 est une projection conservative ; les catégories et preuves
restent dans un second `dmdSec` BBVLM. Un conteneur PREMIS 3 décrit quatre objets
de fichier, un événement d'export et l'agent logiciel. PREMIS passe le XSD
officiel mis en cache (SHA-256 du schéma :
`03b8a77a20b32b882ad799e12262671d07ad18210c60233f4e613a1289491cba`).
Le XSD MODS 3.8 officiel répond 403 dans cet environnement : seule la structure
du profil local est contrôlée, et le rapport conserve `mods_3_8_xsd_valid=false`.
La suite compte 54 tests réussis et un fixture portable omis.

## A18/A19 — référence externe et voie sans réseau OCR

`audit_sbb_reference_a18.py` fige huit ouvrages distincts sur les noms, conserve
quatre réserves non ouvertes et vérifie les blobs Git des quatre images/XML
d'audit. Les 94 lignes/623 mots n'ont pas les défauts structurels massifs des
références précédentes. 16 crops sont lus par Luna sans GT ; Sol reprend les
dix incertitudes dans `sol-input`, avec masque de ligne et image originale.
Le score conserve le texte SBB initial et signale les conventions PUA, sans
normalisation opportuniste. Quatre panneaux source/propositions inspectés.

`bbvlm.gap_alignment.locate_words_without_recognizer` ne prend ni logits ni
boîtes mot. Il utilise le polygone de ligne, le texte final et les espaces de
projection, propose des boîtes ou s'abstient. Aucun réseau de reconnaissance
n'est chargé. Une proposition reste non certifiée ; ce chemin n'est pas activé
par défaut dans l'export de production. Trois tests couvrent coordonnées,
ambiguïté, blanc et rejet des tokens invalides. Total : 57 tests réussis, 1 omis.

A19 trouve 50/94 lignes proposées sous entrées oracle SBB, mais neuf mots très
mal placés. La voie rapide est donc un prototype d'économie à comparer au CTC,
pas un gain certifié. `ARCHITECTURE_A19.md` exige aussi la comparaison VLM texte
seul / texte+relations+preuves à budget visuel identique et une mesure du coût
marginal complet, incluant les reprises et la vérification humaine.
# A20/A21 — explicit OCR convention views and routing diagnostic

`src/bbvlm/ocr_conventions.py` provides strict and versioned glyph-decomposition
evaluation views. No in-place transcription/export mutation. Unknown private-use
characters survive. `scripts/evaluate_ocr_conventions_a20.py` evaluates consumed
A18 output under three explicit views and reproduces the original strict scores.
The broad compatibility view reads only dictionary literals from pinned source
via AST; downloaded Python is never executed. Sources and license are bundled.

`scripts/prepare_routing_a21.py` uses the A18 mask builder for all six Luna
not-uncertain lines. `scripts/evaluate_routing_a21.py` enforces exact IDs and
image-inspection evidence, compares every changed line and counts regressions,
preserving original GT/predictions and the unopened reserve. It records an
additional real Sol reading task, unknown token/billing cost, and model/prompt/
presentation confounds. This does not enable production confidence-only routing.

## A22 — work-disjoint reserve evaluation

`prepare_sbb_reserve_a22.py` opens only the four pre-frozen reserve works,
verifies Git blobs, samples four line IDs per work and makes isolated/context
crops with opaque IDs. `evaluate_sbb_reserve_a22.py` requires exact response
coverage and actual inspection paths, reproduces strict/decomposed code-point
CER and whitespace-token WER, then invokes unchanged A19 localization using
only image, oracle line polygon and Sol token sequence. Geometry uses optimal
one-to-one IoU matching and includes abstentions in recall. All protected inputs
are hashed before/after.

Observed: 16 lines/121 words; one Sol task, 32 images; CER 11.62% strict and
4.86% decomposed. A19 proposes 7 boxes on two lines, mean IoU .971, precision
1.0 at IoU .8, recall .0579. Development→reserve proposal coverage falls
.532→.125 (exploratory Fisher p=.00262). `inspect_sbb_reserve_a22.py` renders
all seven proposals; post-score visual audit finds them plausible but is not
independent human adjudication. No parameters are promoted or changed.

## A23/A24 — ciblage du CTC et entrée VLM multiscalaire

`evaluate_ctc_fallback_a23.py` construit quatre `PageLayout` limités aux lignes
A22, désactive ParseNet et exécute uniquement cropper+OCR PERO. Les logits sont
mis en cache en NPZ/PAGE avec empreintes. Le texte Sol passe par un proxy codec
NFC strictement géométrique ; les tokens et le texte final restent inchangés.
Quatre sorties sont mesurées : PERO natif, CTC forcé, séparateurs CTC + encre,
et fast-path A19 avec repli. Le protocole, les poids et toutes les entrées sont
hachés. Le script de restauration accepte désormais `--only models/pero.zip`,
afin de ne pas télécharger des corpus sans défaut mesuré.

Résultat diagnostique : 16 lignes reconnues en 1,81 s CPU, alignement en 0,13 s.
PERO natif produit 119 boîtes, le CTC forcé 121. Le meilleur hybride gelé obtient
IoU moyen 0,636, rappel IoU≥0,5 de 75,21 % et IoU≥0,8 de 19,83 %. Une analyse
post-score montre que le masque dépassait le rectangle de ligne ; clipping et
Otsu progressent mais sont étiquetés post-hoc et non promus.

`prepare_vlm_input_a24.py` fabrique sans texte de référence un composite par ID :
page localisatrice, contexte 2x, ligne 4x. Une tâche Sol inspecte les 16 images ;
`evaluate_vlm_input_a24.py` vérifie IDs et chemins. Le CER se dégrade légèrement
par rapport à A22. Cette entrée n'est pas retenue et ne rouvre pas la réserve.
La suite reste à 61 tests réussis et un fixture volumineux omis ; ces tests
vérifient les contrats logiciels, pas la perfection OCR ou géométrique.

## A25 — validation conditionnelle CTC/Otsu

`freeze_french_holdout_a25.py` gèle les chemins/blobs de quatre pages inédites
avant ouverture. `open_french_holdout_a25.py` télécharge les huit fichiers à la
révision Git épinglée et vérifie chaque identité blob. L'évaluateur construit
des lignes PERO à partir des polygones PAGE, désactive ParseNet, met en cache les
logits, aligne un proxy codec du texte source, puis calcule un Otsu unique dans
le rectangle de chaque ligne. Les milieux CTC fixent les cellules ; les pixels
d'encre fixent les quatre bords. ALTO natif et forcé, boîtes, proxy, timings et
empreintes sont conservés.

Le script exact n'avait pas été haché avant l'ouverture : le rapport porte
`implementation_frozen_before_source_open=false` et reste hors gate. Il révèle
aussi que le lot nommé « french » est allemand. L'expérience complète néanmoins
une itération CPU réelle : 140 lignes en 24,48 s, 1,13 s d'alignement, 1 097
boîtes, rappel IoU≥0,8 de 84,41 % contre 16,77 % pour PERO natif. L'étape A26
devra sceller protocole, script et split multi-ouvrages avant toute ouverture.

## A26/A27 — échec fermé au niveau mot et passe OLR aveugle

`download_bnf_corrected_archive_a26.py` reproduit le téléchargement public BnF
et enregistre le manifeste ZIP sans ouvrir les membres. A26 a ensuite scellé
quatre pages avant extraction, mais l'évaluateur a rencontré zéro ligne et zéro
mot. Son gate vide est conservé comme défaut reproductible puis explicitement
rejeté dans `bnf-impact-a26/FAILURE.md`.

A27 réemploie une page encore fermée et scelle protocole, prompt, préparateur,
évaluateur et cœurs d'ordre avant ouverture. Le préparateur remappe les 235
`TextRegion` vers des tokens opaques aléatoires, rend une page brute, une page
étiquetée et six panneaux de colonnes. Une seule tâche Luna voit uniquement ces
images et doit fournir rôles, flux éditoriaux et ordre. L'évaluation compare ces
flux aux `OrderedGroup` PAGE, avec échec fermé si la référence est vide, et une
baseline géométrique optimiste utilisant les rôles PAGE oracle. Elle n'appelle
jamais ces groupes des articles et ne mesure ni OCR ni boîtes mot.

L'architecture qui se dessine n'est donc pas « PERO complet + VLM ». Les
polygones de régions/lignes peuvent venir du meilleur étage local mesuré ; le
VLM sert là où la vision sémantique ajoute une information absente du CTC
(titres, continuités inter-colonnes, flux, entités et preuves). Le CTC reste un
alignement/localiseur de mots ciblé et le seuillage d'encre fixe les extents.
Les métadonnées issues du classeur BnF (titre, date, ARK) restent des assertions
sourcées et ne sont pas inférées quand une autorité existe.

## A28 — exécution française scellée

`freeze_french_word_gt_a28.py` sélectionne les huit pages des deux œuvres
cataloguées françaises depuis l'arbre Git épinglé et scelle le wrapper, le
candidat A25 inchangé, l'ouvreur et le protocole. `open_french_word_gt_a28.py`
vérifie les 16 blobs. `evaluate_french_word_gt_a28.py` exécute 261 forwards de
reconnaissance CPU en 36,34 s puis 2,55 s d'alignement, calcule les métriques
globales et par page et échoue fermé sur référence vide.

Résultat : 1 753/1 753 boîtes émises ; IoU moyen 0,8388, rappel IoU≥0,5 0,9344
et IoU≥0,8 0,6845. Le gate conditionnel est faux. Le post-audit séparé rend les
40 pires superpositions sans modifier candidat ni GT. Le défaut principal est
vertical (encre voisine/verso dans le rectangle de ligne), ce qui oriente une
future variante vers composantes connexes et bande de baseline plutôt que vers
un nouvel étage PERO complet.

La reprise Sol A27, déclenchée uniquement après les 234 singletons Luna, utilise
les mêmes pixels et tokens sans lire la sortie Luna ni la GT. Le rapport séparé
`sol-escalation-report.json` obtient F1 de flux 0,5906 et rappel d'ordre de bout
en bout 0,4190. Ses 34 flux sont tous des sous-ensembles purs des 13 groupes de
référence : le défaut est une sur-segmentation sans fausse fusion. La passe VLM
apporte donc bien un graphe sémantique plus précis que la baseline (F1 0,5052),
mais un étage CPU de fusion reste à inventer et valider hors A27.

A29 implémente cet étage dans `src/bbvlm/olr_continuation.py`. Il ne re-classe
ni ne réordonne : il fusionne seulement deux flux VLM adjacents lorsque leurs
boîtes terminale/initiale se recouvrent horizontalement à 60 % et que leur gap
vertical ne dépasse pas 0,7 % de la largeur de page. Tests unitaires : entrées
vides, géométrie manquante et refus des colonnes disjointes. Les paramètres
sont hachés avant ouverture de 00123453.

La validation montre un gain F1 0,7132→0,7443, sans fusion impure, mais pas la
fermeture attendue : 15 flux contre 11, six régions éditoriales omises et rappel
d'ordre 0,5918. Le module reste donc un fast-path de précision, jamais une
certification OLR. Aucune seconde passe Sol n'est lancée : le défaut n'est pas
une réponse mal formée mais une insuffisance mesurée de l'hypothèse figée.

## A30 — protocole OCR de région et escalade aveugle

`freeze_bnf_region_ocr_a30.py` fixe page, sélection, code, métrique et archive
avant ouverture. `prepare_bnf_region_ocr_a30.py` extrait 16 régions polygonales,
masque l'extérieur, ajoute 12 px de contexte et agrandit les petits crops à
1 200 px sans exposer le texte PAGE. Luna inspecte les 16 images une fois ;
`evaluate_bnf_region_ocr_a30.py`, scellé, calcule le CER NFC diplomatique.

Après échec du seuil zéro, Sol relit aveuglément toutes les images sans accès à
la référence, Luna ou ses erreurs. `evaluate_bnf_region_ocr_a30_sol.py` conserve
ce résultat dans un rapport distinct explicitement post-hoc. Le script
`audit_bnf_region_ocr_a30.py` ajoute une vue retrieval qui unifie les variantes
de tirets avant de joindre les césures ; il ne modifie pas la métrique scellée.
Résultats : Luna 1,7310 % strict / 0,8440 % retrieval ; Sol 1,4647 % / 0,5739 %.
Les deux restent hors gate et aucun mélange sélectionné par la GT n'est exporté.

## A31 — comparaison d'entrées non masquées

`prepare_unmasked_a31.py` conserve les rectangles A30 et le redimensionnement
cubique 1 200 px, enlève masque/contour et ajoute une image de contexte par
cible (65 px verticalement, 12 latéralement). `evaluate_unmasked_a31.py` vérifie
les 16 IDs, les 32 chemins déclarés inspectés et les SHA-256, puis compare les
deux Sol à la même référence sous normalisation A30 inchangée. Gain net d'une
édition (17→16), trois régions améliorées et deux régressées. Les réponses
brutes sont conservées ; aucun best-of choisi par référence. La boucle comprend
82 phases, toutes terminées ; les sept gates globaux restent faux.
# Ajout A32 — raffinement CPU expérimental, non activé en production

`bbvlm.component_boxes` filtre l'encre par composantes, bande de corps inférée
et satellites. `evaluate_component_boxes_a32.py` mesure trois ablations sur
1 753 mots A28 consommés; `audit_component_boxes_a32.py` rend des triptyques
sans contours sur les pixels. La meilleure variante gagne 13,29 points de
rappel IoU80 contre Otsu pour 0,726 s supplémentaire, mais perd notamment des
ponctuations. Pas de nouvelle passe OCR/VLM, pas de modification GT, pas de
promotion production. Lignes et texte oracle restent une limitation centrale.
Sources/paramètres/code initial et corrigé/résultats sont archivés. La boucle
compte maintenant 84 phases; les sept gates finaux restent faux.
# Ajout A33 — branche expérimentale rejetée

`refine_cells_text` essaie, sur demande du token, de rattacher une petite
composante rejetée à gauche/droite dans l'étendue CTC. Deux ablations, trois
tests synthétiques et une inspection exhaustive sont conservés. Sur 1 753 mots,
4 gains mais 7 pertes et un léger recul agrégé : fonction gardée pour
reproductibilité, non appelée en production. A32 demeure le candidat de
développement. 85 phases terminées; les sept gates finaux restent faux.

# Ajout A34 — transfert multi-ouvrages et échec fermé

`freeze_word_transfer_a34.py` sélectionne par SHA-256 trois œuvres de quatre
pages dans l'arbre SBB épinglé, après exclusion de tout ouvrage A18/A25/A28.
`open_word_transfer_a34.py` télécharge et vérifie les blobs PAGE/TIFF.
`evaluate_word_transfer_a34.py` exécute le même recognizer/alignement CTC puis
compare PERO natif, CTC forcé, Otsu, A32 et A34 au niveau global, page et œuvre.

`refine_cells_text` accepte maintenant une aire minimale de sauvetage et un
ensemble de ponctuation terminale configurables; ses valeurs par défaut
reproduisent A33. A34 fixe aire ≥20 et exclut `*`. Le test synthétique garantit
que cette configuration refuse un blob de 9 pixels et ne déclenche pas sur
étoile. En validation, elle change sept boîtes, une en mieux et six en pire;
elle reste donc inactive. A32 atteint 0,8123 d'IoU moyen et 58,94 % de rappel
IoU80 contre 0,6549/19,04 % pour PERO natif, sous lignes/texte/ordre oracle.

Un export PERO sans ligne OCR vide a révélé un défaut du binder. L'adaptateur
A34 encode explicitement la ligne `E` comme zéro mot natif, sans décaler les
IDs ni supprimer la référence. Cette correction et une clé d'empreinte
redondante ont été ajoutées après ouverture mais avant score : l'invariant
complet de gel vaut faux, même si la règle candidate n'a pas changé. La boucle
compte 88 phases; aucun gate final n'est satisfait.


## A35: recognized-word geometry ablation

2026-09-27: `scripts/evaluate_native_refinement_a35.py` applies unchanged A32 to cached native recognized words. On consumed French A28, recall IoU≥0.8 improves 11.07% → 80.66%; on consumed German/Latin A34, 19.04% → 55.96%. Reference transcription/token count are removed from the refiner; reference line rectangles and synthetic baselines remain. No new OCR/VLM inference or CER improvement. Joint exact-text+IoU≥0.8 recall is 73.25% / 42.09%, and visual audit confirms neighboring-ink/punctuation failures. All project gates stay false. See `experiments/loop/native-refinement-a35/RESULTS.md`, `SOURCES.md`, `PROTOCOL.md` and raw measurements. Next: predicted lines plus an unopened reference set, without retuning these consumed pages.

## A36 predicted-line integration

Full-page PERO predictions are sealed before reference loading and evaluated by
page-wide Hungarian geometry assignment. `nonexpanding_vertical` keeps A32 only
when vertical extent does not grow; on consumed A36 it reaches .698075 mean IoU
versus .648489 native and .639549 unconditional A32. Validation on A37 remains
required; no OCR, OLR, metadata or retrieval claim follows.

## A37 frozen non-expanding router validation

`scripts/run_predicted_lines_a37.py` applies the unchanged A36 router before
any PAGE reference is parsed. On four newly selected pages, the routed boxes
improve native PERO on every page and aggregate mean IoU from .568214 to
.853595; IoU80 recall rises from .005085 to .686441. The complete-page cost is
10.573 s CPU plus .284 s refinement/routing and zero VLM passes. Eleven local
regressions remain, dominated by punctuation/small-glyph conventions plus one
horizontal ownership failure. The component is locally validated, not perfect
or cross-domain validated; all project gates remain false.

## A38–A40 rejected global ownership guards

Three zero-parameter refinements were measured only on consumed cached outputs.
Forbidding width expansion (A38) destroys legitimate recovery from approximate
CTC spans. Requiring full vertical containment (A39) also regresses every
dataset. Rejecting only equal-height vertical translations (A40) is nearly
neutral on A37 but still loses on A28/A34/A36. None is promoted. The A37
height-only router remains the implementation candidate; the next hypothesis
must use local image/baseline ambiguity evidence, not a global rectangle rule.

## A41–A43 rejected local ownership guards

`line_band_excess` and `nonworsening_line_band` provide a reproducible A41
ablation over PERO's predicted baseline and `heights_v2`. Two standalone image
experiments then score Otsu foreground by nearest predicted line centre: A42
uses the whole box, A43 only newly added pixels with a strict-majority rule.
All are reference-free at routing time and add no OCR/VLM pass. They reduce
the number of regressions but also discard more correct refinements; none meets
the frozen noninferiority gate on consumed A36/A37. They remain rejected
research code. Production continues to use only `nonexpanding_vertical`.

## A44 component-majority router and A45 independent reference

`evaluate_component_majority_router_a44.py` vectorizes pixel-to-line distances,
labels connected components once per predicted line crop, and rejects an A37
candidate only when it newly introduces a whole component majority-owned by a
different line. It reduces regression counts but fails the preregistered
noninferiority gate, so it is not called by production code.

`fetch_bnl_independent_a45.py` reads a remote ZIP central directory and only the
48 pre-frozen XML/PNG members with HTTP byte ranges, verifies uncompressed size
and CRC32, and never downloads the full 1.9 GiB archive.
`audit_bnl_independent_a45.py` validates ALTO/image containment, counts the
sample and describes fixed language strata. The new scripts are deterministic;
the language label is descriptive and cannot change the frozen membership.
A45 inference remains pending so the benchmark is still pristine.

## A46 corrected transfer and A47 blind residual audit

`run_bnl_independent_a46.py` executes PERO 0.7.0 once on the 24 frozen blocks,
then applies the unchanged A37 `nonexpanding_vertical` router. Predictions are
sealed before `evaluate_bnl_independent_a46.py` opens XML. The evaluator now
validates `MeasurementUnit=mm10` and converts reference rectangles to 300-PPI
PNG coordinates by `300/254`. The original unscaled report is preserved and
marked invalid in `AMENDMENT.json`.

On 12 French blocks, line recall at IoU50 is 99.52%. A37 raises word-box mean
IoU from .55118 to .61588 and IoU50 recall from .66965 to .73584; word boxes
remain diagnostic. PERO reaches .22438% punctuation/space-free lexical CER
(18 edits, 9/12 exact blocks), not zero.

`retrieval_fold_v1` is a separate NFKD/casefold/accent-insensitive alphanumeric
key. It never overwrites diplomatic text and is frozen for future retrieval
evaluation. `evaluate_bnl_vlm_a47.py` scores two blind readers only on known
A46 residuals. Raw outputs are preserved; this targeted audit cannot be used as
a representative CER estimate or merged into A46.

## A48–A49: recurrent columns and semantic anchors

`infer_recurrent_column_order` replaces chained left-edge clustering with
recurrent `TEXT`/`ILLUSTRATEDTEXT` left-edge modes. A48 was development-only;
all parameters were frozen before six A49 pages were opened. On A49, global
pair order improves .672118→.883394, within-article order .871682→.987996 and
article-pair F1 .203237→.663213. The .90/.98/.80 gates are not all met, so this
is not the final OLR system.

One Luna pass over 33 opaque anchors on a consumed A48 page finds seven columns,
covers all 20 reference articles having an anchor, transcribes 19/21 headlines
exactly under `retrieval_fold_v1` against provider OCR, and extracts newspaper,
date, edition and price with evidence. Its article order is only .763158. Keep
geometry for physical order; spend the VLM pass on titles, editorial roles,
inter-page continuations and metadata. Body OCR should run on article crops and
be aligned back to ALTO lines/words by the selective CTC path.

## A50–A51: selective semantic boundary stage

`prepare_finlam_boundaries_a50.py` materializes only geometry-routed candidate
transitions as paired visual crops with opaque IDs. `evaluate_finlam_boundaries_a50.py`
adds Luna’s `new_article` decisions to the existing title cuts while preserving
the recurrent geometry order. On consumed row 186, article-pair F1 improves
.586923→.909293 with one pass over nine sheets.

The A50 router used reference presence to omit unannotated edges and is therefore
development-only. `prepare_finlam_boundaries_a51.py` removes that dependency:
candidate routing reads only region roles and geometry. A51 was frozen before
content opening; two rows are a pilot and six remain reserved. This stage emits
logical article boundaries for METS/structMap, while ALTO retains physical
regions, lines and strings. It does not ask the VLM for pixel coordinates.

The two-page A51 pilot is negative overall: candidate article-pair F1 is
.4823 versus .4876 for title cuts, with a strong row-216 gain but a severe
row-164 regression. Finlam row 164 groups hundreds of visually distinct zones
inside two provider articles, so “provider article” and “retrievable semantic
item” cannot remain a single hidden variable. The next implementation must
encode them as separate logical hierarchy levels, preserving physical ALTO and
immutable provider labels. The six unopened A51 rows remain reserved until
that ontology and its two scorers are frozen.

`experiments/loop/PAPER_SUMMARIES.md` is now the mandatory per-paper review
ledger. `experiments/loop/CLAUDE_BRANCH_AUDIT.md` records the concurrent-branch
inspection that must precede each new hypothesis.

## A57 — checkpoint extensions

`autonomous_loop.checkpoint()` preserves externally registered evidence and phase IDs, refreshes known legacy entries, verifies extra result paths, deduplicates research notes, and never inherits old completion flags. A targeted regression test verifies repeated saves and missing artifacts. This repairs A54-A56 evidence loss during bundling.

## A58
Audit PAGE exhaustif sans afficher les transcriptions : scripts/audit_chronicling_a58.py ; provenance et reserve : scripts/finalize_chronicling_a58.py. Originaux conservés, faute de nom du split signalée mais non corrigée.


## A59
Ajout scripts/evaluate_bnl_sol_a59.py : validation stricte des IDs, images inspectées et hash ; comparaison trois vues normalisées figées A54 ; écarts lexicaux conservés pour adjudication.

