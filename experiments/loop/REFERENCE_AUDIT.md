# Audit des références — résultat bloquant

2026-09-26. Le dépôt Zenodo 4293602 décrit des textes soigneusement corrigés.
Les fichiers PAGE portent le statut Transkribus `GT`. Ce statut n'est pas une
preuve suffisante pour chaque niveau d'annotation.

Constat visuel et XML sur la page 0253902-001 :

- `tl_265` (crop prédit `L4a9c8152d8`) : le XML porte
  `vail'LïiiiiïiieiJ a ;,o h service.` ; l'image montre nettement
  `vaillamment à son service.`. Les niveaux région, ligne et mot contiennent
  cette transcription fautive. Ce n'est donc pas un simple choix du mauvais
  niveau TextEquiv. La lecture Luna est ici fidèle à l'image mais pénalisée.
- `Lfc69267142` : la référence commence par un tilde combinant et `jesophie` ;
  l'image montre `losophie`, continuation de ligne. À contrôler sur page complète.
- Apostrophe ASCII dans les références, courbe dans les sorties Luna : une partie
  du CER strict mesure une différence de convention de sérialisation.
- Les pires baisses d'IoU G01 révèlent aussi des marges de référence variables,
  et parfois une contraction qui coupe une hampe. Voir largest-regressions.png
  (vert référence, rouge PERO, bleu candidat). Le gain moyen ne suffit pas.

Conséquences :

1. Conserver sans modification les fichiers distribués, empreintes et scores.
2. Nommer les chiffres « accord avec les annotations distribuées », pas qualité
   absolue ou vérité terrain parfaite.
3. Les références textuelles bruitées affectent aussi l'expérience d'alignement
   conditionnel : le texte fourni n'est pas toujours une transcription correcte.
4. Ne pas corriger uniquement les exemples où notre système perd : audit d'un
   échantillon aléatoire indépendant, règles de transcription et de boîtes figées,
   puis adjudication séparée avant une nouvelle validation.
5. Une correction proposée par le modèle après examen du test reste une
   proposition à arbitrer, pas une nouvelle référence indépendante.
6. Séparer : intégrité technique, fidélité graphique, fidélité textuelle,
   cohérence documentaire et qualité des annotations de référence.

Les résultats G01 restent reproductibles et prometteurs, mais n'ouvrent pas le
critère global de supériorité. La boucle doit rechercher une seconde référence
mieux documentée et auditer les conventions de mots et les cas d'échec.

## Audit aléatoire aveugle v1 — 27 septembre 2026

Protocole figé avant lecture : 15 lignes non vides tirées uniformément sur chacune
des trois pages avec mots (45 lignes, graine 20260927). La sélection n'utilise ni
texte, ni désaccord, ni difficulté OCR. Les IDs sont hachés. Luna voit seulement
les crops et effectue une passe diplomatique ; les textes distribués et PERO sont
chargés après sauvegarde de sa réponse.

- Accord strict avec le distribué : Luna 14/45 ; PERO 15/45.
- Accord typographique : Luna 17/45 ; PERO 15/45 ; Luna/PERO 28/45.
- Vue recherche (casse/ponctuation neutralisées) : Luna 23/45 ; PERO 21/45 ;
  Luna/PERO 30/45.
- Sur 24/45 lignes, Luna et PERO sont identiques ou plus proches entre eux que du
  texte distribué. Signal de triage 53,3 %, Wilson 95 % [39,1 %, 67,1 %]. Il ne
  décide pas automatiquement qu'ils ont raison, mais invalide le corpus comme
  arbitre textuel suffisant pour une annonce de supériorité.
- Contrôle XML sur les huit pages : 5 493 lignes, 14 365 mots, 12 lignes vides,
  aucune divergence interne ligne/mots sur les trois pages au mot. La cohérence
  interne propage donc aussi les fautes. Une page contient 121 caractères de
  contrôle C1 dans 60 lignes ; ils forment des séquences UTF-8 décodées comme
  Latin-1 récupérables (`â` → `—`, `â¢` → `•`, etc.). C'est un défaut objectif.

Les profils strict, typographique et recherche restent séparés dans `report.json`.
Les 45 sorties et les lignes incertaines sont conservées ; aucune n'est promue en
GT. La suite exige soit une adjudication humaine indépendante sur échantillon
aléatoire, soit un autre corpus à curation mieux documentée.

## Références candidates distinctes

- *The Spiritualist Enriched* : 49 pages d'un journal britannique du XIXe siècle,
  19 691 lignes et 175 548 mots, ALTO au mot corrigé manuellement, plus 425 unités
  sémantiques, classes, colonnes et ordre. Très pertinent pour boîtes/OLR/articles,
  mais anglais et seulement 49 pages ; les boîtes caractère sont inférées.
- `OCR-D-GT-VD-SBB` : 348 pages de 67 ouvrages, PAGE-XML niveau 3, post-correction
  par la Staatsbibliothek zu Berlin, inspection manuelle page par page, exactitude
  annoncée de 99,95 %. Très pertinent pour OCR/conventions et diversité historique,
  mais majoritairement livres allemands/latins et non presse française.

Ces deux corpus couvrent des risques complémentaires ; aucun ne suffit seul à
certifier BBVLM sur la presse patrimoniale française.

## Audit Spiritualist v1 — 27 septembre 2026

Les 49 ALTO de la révision `0f3ddfda…` ont été téléchargés et audités avant
toute inférence sur les pages de validation. Un split aléatoire par noms de
fichiers seulement est figé : 4 pages développement, 8 validation, 37 restantes.

Résultat bloquant pour la géométrie au mot : sur 175 548 `String`, 153 916
(87,68 %) chevauchent leur voisin horizontal d'au moins 25 % de la largeur du
plus petit mot, et 20 521 (11,69 %) sortent de la boîte de leur ligne. L'overlay
de la page de développement 0009 confirme visuellement que les rectangles
recouvrent plusieurs mots. Ce comportement est cohérent avec une position
inférée/distribuée, pas avec des boîtes manuellement détourées. Ces boîtes sont
donc **rejetées comme VT indépendante** pour PERO/G01/G02.

Les 49 XML échouent aussi au XSD ALTO 4.4 non modifié : chacun des 905
`TextBlock` utilise cinq attributs non normatifs (`BLOCK_TYPE`, `COLUMN_ID`,
`READING_ORDER`, `SEMANTIC_ID`, `SSU_ID`), soit 4 525 erreurs. Ces informations
restent utiles, mais doivent entrer dans le graphe de preuves et être projetées
en ALTO/METS normalisés plutôt que copiées telles quelles.

Aspects conservés avec réserve : 19 691 lignes, texte déclaré corrigé
manuellement, 425 SSU, 672 arêtes d'ordre importables et aucun doublon d'ordre
non négatif. Le pilote d'import 0009 met en quarantaine 2 507 boîtes au mot,
conserve 268 lignes comme non alignées, importe 6 SSU et 5 arêtes, résout
explicitement l'image par empreinte, puis produit ALTO 4.4 et METS 1.12.1 valides.
Aucun SSU n'est automatiquement promu en article.

Pilote OLR aveugle sur cette même page de développement : IDs hachés sans fuite
d'ordre, une seule passe Luna. La réponse brute échoue la contrainte d'identité
à cause d'un caractère omis dans un ID ; aucun score ne passe donc le gate.
Après réparation déterministe uniquement pour diagnostic, l'ordre des 6 régions
ayant une référence non négative est correct sur 15/15 paires, mais les 6 SSU
sont fusionnées en 3 (F1 par paires 0,774) et le rôle exact n'est correct que sur
7/12 régions. Cela montre qu'une passe globale peut être utile pour l'ordre et
la continuité narrative, mais ne fournit ni transport d'ID fiable ni typage
documentaire suffisant sans contrainte/validation.

## Validation OLR A03 — jetons liés, pages 0003 et 0008

Les deux pages ont été sélectionnées dans le split gelé avant inspection et sont
maintenant consommées. Luna a vu une fois les originaux et overlays, jamais les
XML, références ni tables de liaison. Les jetons courts aléatoires ont été rendus
exactement une fois dans ordre, groupes et rôles : la réponse brute est valide,
sans réparation, puis liée par logiciel aux IDs stables.

Le contenu ne passe toutefois aucun gate de page. Page 0003 : ordre par paires
16/28 (0,571), F1 SSU 0,526, rôles 7/12. Page 0008 : ordre 311/351 (0,886),
F1 SSU 0,478, rôles 23/30. Agrégat micro : ordre 0,863, F1 SSU 0,492, rôles
0,714. La référence ordonne essentiellement des colonnes entières ; Luna place
correctement beaucoup d'éléments mais intervertit des flux de colonnes. Il
fusionne aussi des annonces que la distribution sépare en SSU unitaires et
classe plusieurs fragments de manchette comme `OTHER`.

Ces désaccords peuvent mélanger erreur du modèle et convention annotative : les
labels distribués n'ont pas été adjudiqués indépendamment. Ils restent donc des
accords avec une proposition de structure, pas une mesure de vérité absolue. La
suite doit figer un profil de convention à partir du développement seulement,
préserver l'abstention, et utiliser d'autres pages pour tout test indépendant.

## Validation d'ordre A04 — page 0014

L'audit des pages de développement révèle que `READING_ORDER` suit exactement
les colonnes gauche→droite, puis les régions haut→bas ; ce champ n'encode donc
pas à lui seul une lecture sémantique complexe. Un ordonnanceur géométrique sans
`COLUMN_ID`, texte, rôle ni VLM a été sélectionné sur 0009/0038/0041/0043, puis
figé avant 0014. Il obtient 378/378 paires sur cette page, contre 299/378 pour un
tri global haut→bas et 300/378 pour un tri global x→y.

Ce succès mesure la reproduction d'une convention physique sur des `TextBlock`
fournis. Il ne valide pas les régions prédites, les articles, les SSU ou la vérité
éditoriale de l'ordre. La page 0014 est désormais consommée pour cette tâche.
L'ordre colonnaire peut néanmoins être retiré de la passe VLM normale : le modèle
ne doit être appelé que si la géométrie indique plusieurs flux plausibles ou pour
les relations sémantiques que cette règle ne peut pas produire.

## Validation sémantique A05 — page 0015

Les conventions ont été comptées uniquement sur 0009/0038/0041/0043 avant
préparation de 0015 : MASTHEAD et OTHER y sont exclus du flux, HEADER et TEXT
inclus ; 17 unités associent un en-tête à du texte et aucune unité ne traverse
une colonne. Luna a inspecté une fois original + overlay, avec jetons aléatoires,
sans XML, liaison secrète ni référence.

La réponse brute est structurellement valide. Éligibilité : précision = rappel =
1,0 (19/19, zéro contamination). Rôles : 20/22. Après filtrage, l'ordre A04 fait
171/171 paires. Pour les SSU, Luna prédit 7 unités contre 8, avec 22 vraies
relations, 12 relations ajoutées et 2 manquées : précision 0,647, rappel 0,917,
F1 0,759 ; B-cubed F1 0,870. Le seuil préenregistré de 0,80 par paires échoue.

L'analyse postérieure localise une fusion de deux items successifs dans la
première colonne et un bloc affecté à une mauvaise unité. Elle sert à concevoir
A06 mais ne transforme pas 0015 en nouvelle validation. Les labels Spiritualist
restent proposés et non adjudiqués ; le résultat ne certifie aucun article.

## Validation sémantique A06 — page 0029

La règle CPU de regroupement par `HEADER`, choisie sur les quatre pages de
développement avec F1 macro 1,000, a été figée avant 0029. Deux appels Luna ont
échoué au transfert avant toute réponse ; un troisième, même famille et même
prompt, a utilisé des dérivés d'inspection 1200×1698 et produit l'unique réponse
de contenu. Original, référence cachée, seuils et liaison sont inchangés.

La réponse brute est valide et non réparée. Elle obtient une précision/rappel
d'éligibilité de 0,941/0,696, 17/27 rôles, un F1 SSU de 0,680 et un rappel d'ordre
combiné de 120/253 = 0,474. Tous les seuils de rappel/contenu échouent ; 0029 est
consommée et ne sera pas rescored sous une nouvelle convention.

L'examen après score identifie une incompatibilité de vocabulaire mesuré. Les
jetons E9/Q8 couvrent l'encadré *Charges for Advertisements* et P8/Z4/C9
l'encadré *Wanted a Ghost*. Luna les classe `ADVERT` et les sort du flux ; la
distribution n'a pas de classe éditoriale publicité, encode ces zones comme
`HEADER`/`TEXT` et les ordonne avec le contenu. Cette lecture visuelle est
plausible mais n'est pas une adjudication. Cinq autres désaccords concernent la
granularité masthead/date/ornement/note. La référence Spiritualist peut mesurer
une structure physique interne, pas directement une taxonomie éditoriale riche.

## Validation facettée A07 — page 0039

Le protocole sépare avant inspection rôle physique et genre éditorial. Le genre
ne contrôle jamais l'inclusion et n'est pas scoré : la source ne possède pas
cette vérité terrain. Une seule passe Luna produit deux cartes complètes, sans
ordre, groupe, éligibilité ou transcription.

La correction A06 fonctionne : précision = rappel du flux = 1,000 (21/21, zéro
contamination) et ordre combiné 210/210. Le résultat global reste négatif : Luna
échange cinq HEADER vers TEXT et trois TEXT vers HEADER, plus un UNKNOWN vers
HEADER. L'accord physique vaut 15/24 et le F1 SSU 0,591, malgré 9 unités prédites
pour 9 de référence. Les frontières, non le compte, sont fautives.

L'examen postérieur montre sur 0039 des hauteurs HEADER 35–66 px et TEXT
111–2348 px. Le développement reste moins séparable (HEADER 32–110, TEXT
64–3133). Une calibration développement seule retient 0,020 de la hauteur de
page ; elle est une hypothèse A08, pas une relecture favorable de 0039.

## Validation grossière + géométrie A08 — page 0044

La réponse Luna brute est valide. L'axe grossier obtient 13/13, le flux 10/10,
puis la règle hauteur/page figée obtient 13/13 rôles fins. Les quatre SSU sont
exacts (F1 paires et B-cubed 1,000). Le gate échoue sur l'ordre, 38/45 : A04
fusionne les colonnes médiane et droite. C'est un défaut CPU mesuré ; 0044 ne
sera ni retunée ni renommée test indépendant.

## Validation ordre robuste A09 — page 0050

La passe Luna retrouve 9/9 régions de flux ; l'ordre à trois colonnes obtient
36/36. Un seul rôle fin diffère : un titre multi-ligne haut de 238 px devient
TEXT. Il fusionne deux SSU, F1 0,733. Le seuil hauteur n'est donc pas universel ;
la prochaine hypothèse utilisera les lignes et la typographie interne sur un
nouveau split. Les huit pages de validation initiales sont consommées.

## Portée des références A10–A13

A10/A11 exploitent le texte et les lignes distribués pour les caractéristiques
typographiques : même avec des rôles grossiers lus par Luna, ce sont des tests
conditionnels. A12 ne lit aucune référence pour proposer les colonnes YOLO,
mais son évaluation d'ordre utilise les régions source ; les 415 rectangles de
lignes servent seulement à sonder le risque de crop, pas à certifier l'encre.

A13 est un diagnostic de lecture sur trois petits paragraphes prédits de la
page déjà consommée 0044. Le CER mesure l'accord avec les transcriptions
distribuées ; des signes de ponctuation manquants dans la référence sont à
auditer sur l'image. Une relecture de modèle, même exacte visuellement pour
l'agent principal, n'est pas l'adjudication humaine indépendante requise.

## A14/A15 : conservation, référence et qualité réelle

A14 construit les lignes par une vraie détection PERO et les colonnes depuis
YOLO A12 ; aucune référence ne participe à la construction. Les 418 rectangles
source entrent après sauvegarde. Le même rappel 385/418 avec 416, 496 ou 635
fragments montre pourquoi rappel seul ne suffit pas. Les pertes de surface
sont relatives aux polygones prédits, pas à des caractères disparus.

A15 réutilise Sol A13 (routage assisté par score), lie le texte à 20 lignes
prédites et aligne 184 mots sans lire de XML source. L'audit visuel non
indépendant retrouve des tirets longs hors boîte malgré zéro repli natif.
Ni texte conservé, ni accord de modèles, ni XSD ne certifient la géométrie.
Les mêmes crops ne pourront valider le futur correctif G02.

## A16 : le diagnostic des boîtes de ponctuation n'est pas une référence

Les overlays A16 ont été inspectés après l'enregistrement du défaut A15. Les
quatre extensions prudentes correspondent à de la ponctuation de bord visible,
dont deux cadratins, mais 0044 est consommée et l'inspection n'est pas une
adjudication indépendante. Le masque Otsu prouve de l'encre, pas son appartenance
au mot. Le graphe A15 et les sources restent intacts ; A16 exporte un paquet
séparé, laisse chaque ligne automatique/en revue et reste hors des gates. Il faut
toujours figer un ensemble divers et faire adjudiquer ses boîtes indépendamment.

## A18 — une nouvelle référence réellement téléchargée et auditée

Le 27/09/2026 : OCR-D/OCR-D-GT-VD-SBB, révision
`481f7235acfc1f78e88b3c2f22f551595c3f2032`. Tirage par noms de fichiers et
ouvrages distincts : quatre pages d'audit, quatre pages réservées non ouvertes.
Les huit fichiers image/XML téléchargés passent leur identité Git blob et ont
un SHA-256 conservé. Originaux non modifiés. Sur 94 lignes/623 mots, aucune
boîte de mot hors de sa ligne et aucun chevauchement voisin ≥25 %.

Les quatre panneaux de contrôle ont été réellement inspectés : mots imprimés
en Fraktur et caractères gravés/inclinés. Les boîtes source apparaissent serrées
et plausibles, contrairement au défaut massif Spiritualist. Cela justifie une
référence candidate sérieuse de géométrie, pas le label « parfaite » sur toutes
les pages. Les marges/coordonnées de polygones et la tokenisation nécessitent
encore une convention explicite et une adjudication des cas ambigus.

La fiche institutionnelle annonce prestataire, post-correction SBB, inspection
de chaque page et niveau OCR-D 3. Ce dernier conserve aussi des graphèmes
MUFI/privés : il ne faut pas appeler ces caractères des erreurs de référence.
Le premier test Luna (16 lignes, 707 caractères) obtient un CER strict distribué
de 50,07 %. L'examen postérieur trouve plusieurs transcriptions de lignes
voisines dans les rectangles inclinés et des substitutions de ligatures privées,
en plus de vraies erreurs de lecture. Cette valeur ne permet pas de comparer
proprement les capacités de lecture sous conventions communes.

Les dix incertitudes Luna déclenchent seules la reprise Sol avec isolement du
polygone cible et original accessible. Ni GT ni réponse Luna ne lui sont fournis.
Le résultat est dans `reference-a18/ocr-report.json`. Présentation et modèle
changent ensemble : pas d'attribution causale au modèle seul. La référence n'est
pas réécrite pour atteindre zéro. Aucun score normalisé PUA n'est inventé : il
faut obtenir la table de convention officielle puis la figer pour la réserve.

Résultat sauvegardé : Luna 354/707 éditions (50,07 %) ; Luna+Sol ciblé 92/707
(13,01 %), une ligne exacte sur seize dans les deux cas. La référence contient
29 caractères privés dans onze lignes. La reprise a réduit les transcriptions
de voisins, mais les lectures de glyphes et la fidélité diplomatique ne sont
pas résolues. Une passe Luna (16 crops), une Sol (10 cibles et leurs originaux) ;
tokens/facturation non exposés, donc non chiffrés. Aucun résultat parfait annoncé.

Autre source primaire confirmée : la fiche BnF « OCR corrigé de documents de
presse de Gallica » décrit transcription manuelle et identification des zones,
avec lots Europeana (54 Gallica), interne (121 Gallica), IMPACT (16 Gallica),
NewsEye (135 Gallica). Priorité aux lots non-NewsEye pour diversifier en français.
Ces fichiers ne sont pas encore téléchargés, ni leurs boîtes mot certifiées ;
ne pas leur substituer l'ALTO OCR ordinaire de Gallica. La distribution PRImA ENP
est aussi une piste, pas une référence localement testée dans cette itération.

Attribution SBB : Baierer, Federbusch, Gerber, Lehmann, Neudecker (2025),
DOI 10.5281/zenodo.17395956. La fiche et le README disent CC-BY-4.0, tandis que
le fichier LICENSE du miroir GitHub porte CC-BY-SA-4.0. Les deux indications
sont conservées ; aucune redistribution publique n'est faite ici.

## A20 — référence SBB et encodage (27 septembre 2026)

Le CER doit préciser la convention : 92/707 strict contre 45/736 après
décomposition de glyphes documentée pour les réponses A18 Luna+Sol. Le profil
de compatibilité plus large donne 39/733. Les dénominateurs diffèrent ; aucune
de ces valeurs n'établit une GT parfaite ou une correction du modèle. F1E8
reste présent : une description MUFI indexée a été trouvée, mais le PDF direct
est inaccessible et aucune équivalence diplomatique à '?' n'est présumée.

Des écarts lexicaux et de ponctuation subsistent. A21 examine la fausse confiance
sans adjudication à partir du consensus ; les fichiers GT, réponses A18 et
quatre ouvrages de réserve sont protégés par invariants/empreintes. Une revue
indépendante des cas lisibles contestés reste nécessaire avant toute certification.

## A22 — ouverture contrôlée de la réserve (27 septembre 2026)

Les quatre ouvrages et leurs 16 lignes ont été ouverts après gel du prompt,
des profils et de l'algorithme A19. Blobs Git vérifiés, IDs opaques, 32 images
effectivement inspectées par Sol, réponse brute conservée. La référence compte
121 mots ; les 16 sorties Sol ont par hasard le même nombre de tokens que leur
ligne source, mais cela ne certifie ni identité ni espacement.

Résultat : CER strict 11,62 %, décomposé v1 4,86 %. Les désaccords lisibles ne
sont pas corrigés dans la GT. F519 et F537 sont documentés dans la table OCR-D
comme m avec tilde et ligature ta ; découverte post-score, ils restent inchangés
dans le profil gelé. Le profil v2 devra être figé sur développement puis évalué
sur un nouveau corpus, pas sur cette réserve désormais consommée.

Les sept boîtes émises sont géométriquement plausibles et IoU≥0,8 ; quatorze
lignes sont absentes. L'overlay audite toutes les émissions, mais reste une
inspection par modèle/root et non une adjudication humaine indépendante.

## A23/A24 — réutilisation diagnostique, pas nouvelle réserve

Les images et références A22 restent inchangées et protégées par SHA-256. A23
et A24 les réutilisent après ouverture, uniquement pour isoler deux causes :
fallback CTC et présentation VLM. Aucun de leurs gains ne peut rouvrir le gate
indépendant. La transcription proxy A23 ne sert qu'à la géométrie ; la sortie
Sol originale est conservée intégralement. Le post-traitement Otsu a été observé
après le premier score et est explicitement marqué post-hoc.

A24 confirme aussi que multiplier la résolution et fournir la page entière ne
garantissent pas une lecture exacte : le score se dégrade légèrement. Une GT
future doit figer à la fois les pixels, le niveau diplomatique Unicode, les
espaces/ponctuations et les règles de boîtes avant toute comparaison de modèles.

## A25 — un nom de chemin n'est pas une métadonnée de langue

Le split a été gelé sur les seuls chemins et blobs d'un ouvrage inédit. Après
ouverture, les transcriptions montrent de l'allemand historique et des glyphes
privés, non le français attendu. Le METS du dépôt contient un MODS vide : il ne
permet pas de réparer ce choix après coup. A25 reste utilisable pour comparer
des boîtes conditionnelles, mais pas pour certifier le domaine français.

Les 1 097 polygones de mots sont cohérents avec les textes ligne/mot et donnent
un signal externe beaucoup plus large que A22. Ils restent une GT de projet
prestataire/post-corrigée, non une vérité parfaite adjudiquée. Le candidat Otsu
laisse six mots sous IoU 0,5 et 171 sous IoU 0,8. Les originaux n'ont pas été
modifiés. Toute A26 doit obtenir la langue depuis une fiche bibliographique
fiable ou effectuer un tirage en deux étages où le contrôle de langue ne voit
aucun paramètre candidat, puis figer le code avant les pixels/annotations.

## A26/A27 — deux vérités terrain complémentaires, pas une vérité universelle

Le lot public BnF IMPACT a été téléchargé depuis la fiche institutionnelle
« OCR corrigé de documents de presse de Gallica » : 211 787 980 octets,
SHA-256 `2c8a3e4564c9ffe42270aaf3d6a0d9498b8549b9222fc6d702b751610cc4641c`.
Les 16 PAGE françaises (*L'Aurore*, 1910, et *Le Siècle*, 1869) totalisent
3 432 `TextRegion`, mais zéro `TextLine`, `Word` ou `Glyph`. Le score A26 sur
zéro mot est donc structurellement invalide et son booléen vide est rejeté.
L'évaluateur A27 et son test logiciel échouent désormais fermé sur référence
vide. Aucun original ni annotation n'a été remplacé.

Ces PAGE restent précieux pour les classes de régions et l'ordre : 177
`OrderedGroup` et 3 356 `RegionRefIndexed`. Un `OrderedGroup` n'est toutefois
pas un identifiant d'article documenté. A27 mesure donc des flux ordonnés sous
régions oracle, jamais une vérité d'articles. Le classeur source fournit des
métadonnées fiables au niveau numéro : titre, date et ARK Gallica ; elles seront
exportées comme assertions sourcées, distinctes des inférences visuelles.

L'audit Luna du catalogue OCR-D/SBB a isolé huit pages encore intactes dans les
deux seules œuvres cataloguées `fre`, `borrdisc_689809840` et
`catapabin_657601357`. Leur famille PAGE comporte lignes, mots et glyphes. Elles
forment la prochaine réserve française réelle pour CER/IoU, à geler avant
ouverture. La qualification `fre` et le niveau mot devront encore être vérifiés
après gel ; l'objectif de saisie 99,95 % du producteur ne vaut pas certificat de
perfection.

## A28 — la réserve française au mot est réelle, le candidat n'est pas parfait

Les huit couples PAGE/TIFF des deux œuvres SBB cataloguées `fre` ont été gelés
avec code, protocole et blobs avant téléchargement. Après ouverture, les deux
œuvres contiennent effectivement du français historique ; le catalogue mêle
ponctuellement notices latines et noms propres. La référence exploitable compte
261 lignes et 1 753 mots, avec cohérence exacte ligne = jointure des mots.

Le candidat gelé couvre 1 753/1 753 mots et améliore très fortement les boîtes
PERO natives : rappel IoU≥0,5 93,44 % contre 68,91 %, IoU≥0,8 68,45 % contre
11,07 %, IoU moyen 0,8388 contre 0,5826. Il échoue néanmoins au gate par page :
aucune page n'atteint toutes les exigences, la pire tombe à 40,22 % à IoU≥0,8.
L'audit des 40 pires cas montre que le rectangle Otsu absorbe souvent encre de
ligne voisine ou transparence du verso ; parfois la boîte source et l'extent
d'encre codent simplement des conventions différentes. Ni l'un ni l'autre ne
peut donc être déclaré « parfait » à partir de l'IoU seul.

Le texte PERO natif obtient 4,64 % de CER strict et 2,40 % sous décomposition
de glyphes documentée ; il n'est pas à zéro. A28 n'a lancé aucune passe VLM et
reste conditionnel aux lignes, au texte et à l'ordre de tokens oracle.

## A29 — la convention PAGE inclut des éléments que le lecteur exclut

Sur 273 régions appartenant aux `OrderedGroup`, Luna en retient 267. Les six
omissions sont deux publicités/cadeaux et quatre signatures ou mentions de
source (`Charles Martel`, `MARSIN`, `L. Cama`, `(L'Information)`). Le candidat
n'a pas halluciné de région éditoriale : précision d'éligibilité 1,0, rappel
0,9780. Cette divergence montre que « contenu éditorial » et « membre d'un
groupe PAGE » ne sont pas des conventions interchangeables.

Après raccord, toutes les paires prédites sont contenues dans un seul groupe de
référence ; aucune fausse fusion. Quatre fragments purs excédentaires et les
six omissions suffisent pourtant à limiter F1 à 0,7443. Le résultat est valide
pour mesurer l'accord avec cette annotation, pas pour déclarer des articles
parfaits. L'annotation originale et la sortie Luna sont conservées séparément.

## A30 — une référence manuelle BnF peut encore contenir des anomalies

Le tirage A30 est indépendant des pages OLR consommées et a été ouvert après gel
du protocole, des crops et du score. La référence de région est institutionnelle
et décrite comme manuellement transcrite, mais l'audit post-score relève :

- `T003` contient littéralement U+FFFD dans `judicia�es`, tandis que Luna et Sol
  lisent `judiciaires` ;
- `T014` donne `effaire`, alors que les deux lecteurs donnent `affaire` ;
- `T008` donne `Lé Sénat`, contre `Le Sénat` pour les deux lecteurs ;
- `T006` illustre une frontière de région : tiret/point visibles près du polygone
  mais absents de la transcription source ;
- `T007` mêle apostrophe, tiret initial, nom propre et désaccord verbal.

Ces éléments sont seulement marqués pour adjudication visuelle indépendante.
Ils ne sont ni corrigés ni remplacés par consensus de modèles. Le CER principal
reste donc l'accord exact avec le fichier distribué : Luna 1,7310 %, Sol 1,4647
%. Le rapport secondaire explicite séparément la normalisation retrieval et les
substitutions de codepoints. A30 ne certifie pas une vérité parfaite, mais rend
les causes de désaccord auditables sans contaminer l'original.
# Ajout A32 — ne pas attribuer toute régression à la GT

Sur A28 déjà consommé, l'inspection des originaux et des masques sans overlay
confirme trois pertes du candidat : `M***.` (point), `fertile,` (virgule),
`1725.` (point). Ici la référence est appuyée par l'image. Pour `démon-`, `vée`
et `été`, l'accent principal survit mais des petits fragments supérieurs sont
retirés; leur nature n'est pas tranchée. Le parent a vu les scores avant cette
inspection : audit diagnostique non aveugle, pas adjudication indépendante.
Ni originaux, ni annotations, ni dénominateur ne changent. Voir les images
`component-boxes-a32/regressions-clean.png` et les identifiants dans RESULTS.md.
# Ajout A33 — vérification de chaque rattachement

Les 11 changements ont été inspectés sur les pixels originaux. Quatre signes
réels sont récupérés (`fertile,`, `Law.`, `M***.`, `1725.`); sept boîtes
absorbent un fragment inutile, souvent sous la ligne. Les annotations ne sont
pas corrigées et aucun best-of guidé par la référence n'est exporté. Le constat
d'aire (gains 27–69 pixels, six pertes 5–15) est post-score, donc seulement une
hypothèse à geler avant un nouvel échantillon. `all-changes-clean.png` contient
les pixels sans tracé; RESULTS.md conserve les IDs et la décision de rejet.

# Ajout A34 — « mots » textuels ≠ boîtes de mots

La recherche d'une nouvelle GT indépendante a contrôlé les fichiers, pas
seulement les fiches descriptives. Les exemples DAHN et TAPUS inspectés sont
des ALTO avec `TextLine` et un `String` couvrant la ligne, sans nœud `Word` ou
`Glyph`. L'exemple Reichsanzeiger-GT inspecté comporte 260 `TextLine`, mais lui
aussi zéro `Word`/`Glyph`, malgré les 490 679 « mots » annoncés dans l'article.
Ces ressources peuvent soutenir OCR/ligne; elles ne fournissent pas une vérité
géométrique au mot. Aucune boîte n'a été synthétisée depuis leur texte.

A34 utilise donc trois nouveaux ouvrages SBB à véritables polygones `Word`.
Leur cohérence interne ligne = jointure des mots est vérifiée, mais leur statut
reste celui d'une GT prestataire/post-corrigée, non d'une adjudication parfaite.
Ils sont allemands/latins et livresques : la mesure ne valide pas la presse
française. L'inspection des sept différences A34 confirme une seule ponctuation
bien récupérée et six absorptions d'encre voisine; ni la prédiction ni la GT ne
sont réécrites après cette observation.

Enfin, la règle candidate était scellée avant l'ouverture, mais deux corrections
mécaniques de l'adaptateur ont été nécessaires avant le premier rapport. Le
rapport expose donc honnêtement
`evaluation_adapter_amended_after_open_before_scores=true` et aucun gate projet
n'est accordé.


## A35: remove reference transcription, retain line-oracle limitation

2026-09-27: `scripts/evaluate_native_refinement_a35.py` applies unchanged A32 to cached native recognized words. On consumed French A28, recall IoU≥0.8 improves 11.07% → 80.66%; on consumed German/Latin A34, 19.04% → 55.96%. Reference transcription/token count are removed from the refiner; reference line rectangles and synthetic baselines remain. No new OCR/VLM inference or CER improvement. Joint exact-text+IoU≥0.8 recall is 73.25% / 42.09%, and visual audit confirms neighboring-ink/punctuation failures. All project gates stay false. See `experiments/loop/native-refinement-a35/RESULTS.md`, `SOURCES.md`, `PROTOCOL.md` and raw measurements. Next: predicted lines plus an unopened reference set, without retuning these consumed pages.

## A36 reference status

Selection excluded all earlier works and inference did not read PAGE XML.
Mechanical coordinate and serialization amendments are preserved in
`AMENDMENT.json`, so A36 is not called a pristine implementation freeze.
Provider GT is unchanged and not claimed as perfect adjudicated truth; the work
and router development are now consumed.

## A37 reference status

The A37 code and zero-parameter router were sealed before the selected files
were opened. Git blob identities were verified and inference did not parse PAGE
XML. Unlike A36, no post-open implementation amendment was required. The
provider reference is retained unchanged. Visual inspection of the eleven
routed regressions identifies punctuation/token-boundary conventions in
several cases; this is reported as an evaluation limitation, not used to edit
the GT or rescore the candidate. `curineux_853804893` is now consumed.

A38–A40 use only consumed cached predictions and unchanged provider references.
Their negative comparisons do not alter A37 scores, annotations, or independent
status. No rejected rule is promoted by deleting punctuation/token-convention
cases from a denominator.

## A44–A45 reference status

A44 reuses only consumed A36/A37 references and is rejected. Its lower
regression counts are not used to cherry-pick or remove difficult words, and no
threshold is fitted after scoring.

A45 is frozen before content inspection from the BnL raw newspaper GT archive.
The 24-member sample contains 12 automatically identified French blocks and
10,056 French-reference characters. The BnL documents double-keyed text with a
minimum 99.95% accuracy and recommends the raw pairs for text-line
segmentation. Those claims support independent OCR and line evaluation, while
still implying a nonzero possible reference-error rate. The archive also
contains ALTO word rectangles, but the public description does not say that
every word rectangle was manually adjudicated. A45 therefore cannot by itself
certify perfect ALTO word boxes. Original XML and PNG files remain immutable;
future predictions and normalized scoring views must be stored separately.

## A46–A47 — unit correction and probable BnL text errors

The initial A46 geometry report was invalid because it compared BnL `mm10`
coordinates directly to raster pixels. It is retained as
`report-unscaled-invalid.json`. Applying the declared unit and documented
300-PPI resolution (`300/254`) restores near-complete line agreement and reveals
a genuine A37 word-box improvement, but not perfect boxes.

Only three of twelve French blocks have non-zero punctuation-free lexical CER.
A47 targets those already-known residuals, so it is an audit rather than an
independent performance sample. Blind Luna and subsequent blind Sol agree
under accent-insensitive retrieval folding on all seven images. Visual triage
flags probable provider errors including `sera/fera`, two `II/Il` cases,
`eile/elle`, `a/à`, `impos.-/impos-`, and `précisement/précisément`. It also
confirms real PERO failures such as truncated `— On lit dans...`, `cerlains`,
`daction`, and `arriére`. Model consensus does not amend the source; independent
human adjudication remains required before any zero-CER claim.

## Finlam La Liberté (A48–A49)

Finlam supplies page-level reference polygons, classes, orders, article IDs and
section IDs on an official test split. Its fields are not interchangeable kinds
of truth: `zone_texts` is OCR-extracted provider text, not certified human
transcription; `zone_orders` includes issue-logical inter-page continuations,
not only page-local visual order; and `TITLE`/`SUBTITLE` expresses typographic
hierarchy that can differ from editorial main-title/surtitle semantics. A48/A49
keep annotations immutable and score each layer separately. Luna/reference
agreement is never treated as a perfect-ground-truth certificate.

## Finlam article convention (A50)

The six consumed A49 pages contain 69 reference articles without a `TITLE`
zone; only three (4.35%) span more than one page. The dominant failure is thus
not missing issue context but within-page grouping of advertisements, listings
and briefs represented almost entirely as `TEXT`.

Post-score inspection also finds cases where two visually and semantically
distinct notices share one Finlam article ID. Luna’s corresponding
`new_article` decision counts as a false positive against that immutable
reference even when it is defensible for retrieval. A50/A51 therefore report
both agreement metrics and convention limits; they never rewrite article IDs or
call VLM/reference agreement perfect truth.
