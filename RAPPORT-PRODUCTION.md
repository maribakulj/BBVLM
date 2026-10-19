Cycle17 : V2partielle26758chars, CERv2 30,3207%, strict32,4148%,4/5devmanquantes ; erreur126 puisreprisehumaine127 attestée, VT128+error129/refus130, uncertain=true. V3premièreportion8836charsMORE correctementreçue, arrêt des suivis pour préférenceutilisateurpromptminimal. EssaiV4 lancé, pasencorenoté.347testssnapshotpassent. CTCsource-frame201words2450population14,4s :strictcentre0défautcoord/0refus, mais124supportsminimumchutent>2x etshiftmax77,995px ;NONPROMU, couvertureglyphesnoncertifiée. Toutesréférencesrestenthorsproduction, Axelpréservé, objectifACTIVE.

Le driver v2 a atteint son délai d'observation de900s pendant que Gemini
travaille toujours. Aucun OCR n'a été renvoyé. Un observateur local réel
attend la fin native et vérifie le Markdown identifié avant de reprendre
le même cache. La nouvelle conversation a4bf... est liée au prompt/UUID
exact ; le hint866capturé avant fin de clear était périmé et a été réparé.
Les48vues ont toutes un Read natif terminé ; l'image globale n'a pas été
lue dans cette requête. Aucun résultat textuel v2 n'est encore acquis.

# Cycle 16 — VT indépendante, transport natif et collaboration Astra

253 tests communs passent (8,74 s). La VT de page entière est conservée avant
les refus de géométrie. L'essai v1 direct fournit Fronde36 235 et Matin40 087
caractères, avec provenance Gemini native. Ces sorties restent imparfaites.
Les réponses originales sont récupérées read-only dans SQLite natif ; le
reformatage de Fronde avait changé six opérations et est conservé en
quarantaine. Le terminal perdait le début de ses 1 500 lignes de segments.

Le client a effectivement réduit Fronde7392×9664 à3133×4096 et
Matin4942×6906 à2198×3072, établi par décodage des JPEG du metadata natif et
comparaison des pixels (MADgris1,9998 /3,3147 après redimensionnement source).
Aucune conclusion sur un prétraitement serveur. Le nouvel essai v2 en cours
sur les cinq dev utilise Markdown naturel sans JSON/text_parts, page pour
le contexte et vues1536² source avec overlap192. Il change deux facteurs
ensemble ; aucun gain n'est acquis à ce stade.

Avec le nouveau chargeur textuel entier incluant les tables, v1 Fronde :
CERv2 ordonné3478/35827=9,70776%, strict4043/35817=11,28794% ; Matin :
5101/39133=13,03503%, strict5422/39129=13,85673%. Deux dev mesurées,
trois dev et toutes seize réservées encore manquantes dans cet essai.
Fronde a80lignes de table non vides,617caractères supplémentaires ; deux
TableRegion absentes de l'ordre explicite rendent cet ordre incomplet.
Aucune table/textes supplémentaires supprimés pour améliorer le résultat.
Les anciens scores du chargeur limité à960lignes demeurent historiques.

Astra a intégré alignement/ancres/géométrie/OLR/export séparés (baf704f).
Sa Fronde v1 exporte430/1007lignes contre451ancien, charsnonblancs39,44% ;
CERexport62,098% contre62,025%, IoUmédian0,9571contre0,9583,
p99bords8contre6pixels. Variante non promue. Les430lignes passent les vrais
lecteurs Kraken et le roundtrip Axel13857positions ; cela certifie la
compatibilité technique, pas la qualité. L'ordre des406lignes appariées a
zéro inversion, portée conditionnelle uniquement. Les collisions et refus
restent dans le verdict. Coordination/propriété/exclusivité Gemini décrites
dans COORDINATION.md, aucune modification de fichiers Axel par BBVLM.

L'essai d'échelle complet sur21pages a terminé ; ses seize réservées ont
neuf régressionsF1àIoU0,5 et quatorzeàIoU0,75 contre auto-v2. Non promu.
Le prototype de masque CTC des frames de padding n'est pas intégré ni
promu. L'objectif persistant reste ACTIVE ; les critères initiaux de
couverture, géométrie, ALTO et OLR restent exigés.

# Production autonome — mesures du 6 octobre 2026

L'objectif persistant reste **actif**. La chaîne produit des sorties utilisables
par les lecteurs, mais aucun verdict de VT parfaite n'est acquis. La suite v1
reste composée de 21 pages : 5 de développement et 16 réservées. Deux pages
ont terminé lecture, géométrie, OLR et export, dans des essais distincts ; les autres manquent encore
au verdict. Les résultats complets et les références sont locaux, hors Git,
dans `runs/production-20261006/`.

## Chaîne entière, première page OCR17 de développement

Source : Balzac1624_Lettres_btv1b86262420_corrected_0044/image.png. Aucune
référence transmise à Gemini, au segmenteur, à l'aligneur ou à l'OLR. Les 19
lignes proviennent de la segmentation automatique de l'image entière.

| Mesure | Résultat |
|---|---:|
| Détection des lignes, IoU 0,50 / 0,75 | 19/19, F1 = 1 |
| Lecture conditionnelle stricte NFC | 18/489 erreurs, CER 3,68098 % |
| Lecture conditionnelle, convention v1 | 7/489 erreurs, CER 1,43149 % |
| CER exporté strict, refus inclus | 44/489, 8,99796 % |
| CER exporté, convention v1, refus inclus | 33/489, 6,74847 % |
| Couverture des caractères de référence | 462/489, 94,47853 % |
| Lignes exportées / refusées | 18/19 / 1 |
| Ordre des lignes, Kendall | 1 |
| OLR produite | 1 en-tête, 1 bloc de texte, 1 article |
| Validation ALTO 4.4 et PAGE 2019 | XSD et contrôles de géométrie réussis |
| Lecteurs Kraken 7.1.1 PAGE et ALTO | 18 lignes chacun, textes exacts |
| IR Axel | aller-retour exact, 18 lignes, 464 positions de caractères |

Les éléments Word de cette référence OCR17 sont des **lignes entières**.
Ils ne permettent aucune certification des boîtes de mots. L'OLR produite
n'a pas de référence d'articles/types sur cette page ; son export réussi ne
constitue pas une mesure de détection/classification/regroupement. Les pages
AS réservées serviront à ces mesures séparées.

Les erreurs conventionnelles conservées concernent une ponctuation, des
espaces de ponctuation/mots et un diacritique. La ligne L0012 est refusée pour
ajustement suspect à l'encre. Son texte reste disponible dans annotations.json
et training-excluded.json. Elle compte comme suppression dans le CER exporté.
La lecture v2 est une expérience aveugle terminée sur les mêmes pixels,
avec consignes d'espaces et de diacritiques renforcées. Elle régresse : lecture
conditionnelle stricte 20/489 (4,08998 %), conventionnelle 10/489 (2,04499 %).
L'export reste à 18/19 lignes, CER strict 46/489 (9,40695 %), conventionnel
36/489 (7,36196 %), couverture 94,47853 %. Les deux sorties sont conservées.
L'essai v3 ouvre des recadrages de détails natifs pour chaque ligne large,
sans référence. Il est terminé sans gain : les erreurs conditionnelles sont identiques à v2, en 1 268,6 s.

## Correction d'alphabet, même transcription Gemini rejouée

CATMuS ne peut encoder le s long `ſ`. Un routage strict utilise le modèle
local german_print quand il peut encoder **le texte original**, sans alias
`ſ` → `s` ni suppression. Le modèle est enregistré par ligne.

| Rejeu géométrique, diagnostic séparé | CATMuS seul | Routage strict |
|---|---:|---:|
| Lignes retenues | 8/19 | 16/19 |
| Échecs d'alphabet | 9 | 0 |
| Autres refus | 2 | 3 |
| Couverture des caractères | 40,08180 % | 83,64008 % |
| CER conventionnel exporté | 60,53170 % | 17,17791 % |

Ce tableau isole le changement d'aligneur. Le passage entier ci-dessus ajoute
les reprises Gemini des deux lignes incertaines. Une lecture n'est plus
redemandée pour réparer un alphabet absent : cela risquerait de modifier une
graphie correcte pour satisfaire le moteur.

## Segmentation, page entière de L'Œuvre

| BLLA | Lignes prédites | Correspondances à IoU 0,50 | Rappel | F1 |
|---|---:|---:|---:|---:|
| Global | 178 | 14/363 | 3,85675 % | 0,05176 |
| Tuiles, 339,5 s | 602 | 350/363 | 96,41873 % | 0,72539 |

Il reste **13 omissions et 252 détections sans correspondance**. À IoU 0,75,
les tuiles n'apparient que 163 lignes, F1 = 0,33782. La complétude des références
en dehors des régions annotées reste à auditer ; les détections sans match ne
sont ni supprimées ni toutes qualifiées de texte inventé. Les scores v1 sont
conservés tels quels. Aucun assouplissement de seuil n'a été effectué.

La sélection automatique de résolution estime la hauteur des composantes
d'encre projetée dans BLLA : sous 8 pixels, elle passe aux tuiles. Sur les cinq
pages de développement, elle choisit les tuiles pour les quatre journaux et
le passage global pour OCR17. Cette règle n'a pas encore été validée sur
toutes les pages ; ses décisions sont enregistrées.

Une expérience géométrique complémentaire utilise PP-DocLayoutV3 local :
180 candidats bruts (inférence détecteur 1,60 s), puis BLLA à échelle native
dans 86 fenêtres de régions. Elle produit 575 lignes en 170,6 s. À IoU 0,50,
333/363 sont appariées (rappel 91,73554 %, F1 0,71002), donc **30 omissions** :
le gain de temps ne justifie pas de remplacer les tuiles plus couvrantes.

La rétraction des rectangles sur les composantes d'encre native, avec marge
de 2 px et tous les IDs conservés, donne :

| Variante | Matches IoU 0,50 | Matches IoU 0,75 | F1 à 0,75 |
|---|---:|---:|---:|
| Tuiles originales | 350/363 | 163/363 | 0,33782 |
| Tuiles + encre | 350/363 | 294/363 | 0,60933 |
| Régions originales | 333/363 | 176/363 | 0,37527 |
| Régions + encre | 336/363 | 292/363 | 0,62260 |

Cette correction de bords est une expérience image-only. Le recadrage initial
reste disponible pour lire/aligner sans perdre un accent de bord. La comparaison
fixe des cinq pages de développement est lancée ; la géométrie de mots et ses
cas extrêmes doivent encore être mesurés avant adoption générale.

## OLR non textuelle et contrôles d'export ajoutés

Les illustrations proposées par PP-DocLayoutV3 et les traits longs mesurés
dans le masque d'encre possèdent des IDs et coordonnées de production. Gemini
ne peut fournir aucune coordonnée : il accepte/type chaque ID, le conserve
incertain, ou le rejette avec un motif visuel explicite. L'OLR garde ces refus.
Les blocs s'étendant sur des colonnes disjointes sont scindés géométriquement
sans modifier les articles ni l'ordre déclaré des lignes.

L'export émet Illustration/GraphicalElement en ALTO et ImageRegion/
SeparatorRegion en PAGE, avec références d'ordre vérifiées par les XSD. Les
tests vérifient l'omission/duplication/invention d'un candidat, les colonnes,
les coordonnées d'un trait connu et les refus d'OLR dans le CER final. Cela
valide les contrats d'échange ; aucun score OLR indépendant sur AS n'est encore
acquis. La réparation native 401 est également disponible pour cette passe.

## Reprise et reproductibilité

Le relais enregistre une intention avant soumission, l'UUID, les pixels réels,
le prompt, la réponse validée et les incidents. Les réponses sont mises en
cache par image/IDs/boîtes/échelle/révision. Après timeout ou interruption,
une requête existante est récupérée ; aucune soumission ambiguë n'est répétée.

Un incident réel a été traité : Gemini a tenté un chemin de code inexistant
puis s'est bloqué sur une recherche shell. La recherche a été annulée avec
Esc, l'état done vérifié, puis la **même requête** a été continuée. Aucun texte
ou fichier de référence n'a été fourni. Les requêtes suivantes interdisent
explicitement toute lecture hors des images listées. Une relance de la
commande entière OCR17 a réutilisé les sorties, sans nouvelle lecture Gemini.

Reproduire la sortie existante, après vérification du terminal Gemini :

```sh
/Users/marcel/outils-seg/kraken-env/bin/python src/pipeline.py \
  /Users/marcel/corpus-vt/raw/Balzac1624_Lettres_btv1b86262420_corrected_0044/image.png \
  runs/production-20261006/dev/ocr17-full \
  --gemini-pane w6:p4 --segmentation full
```

Pour de nouvelles pages, `pipeline.py` utilise `--segmentation auto` par défaut.
Les IDs Herdr doivent être redécouverts ; w6:p4 n'est pas une constante.
`scripts/produire_suite.py` accepte exclusivement le manifeste public d'images.
`scripts/evaluer_suite.py` utilise les références en dehors de la production.
Un résultat manquant figure explicitement comme échec/incomplet de la suite.

57 tests passent avec `/Users/marcel/cinoc/.venv/bin/python -m pytest -q tests`.
Les 41 artefacts du pilote ont été vérifiés contre leur manifeste SHA-256.
Aucun fichier Axel n'a été modifié par ce travail ; ses modifications actives,
dont uv.lock, restent préservées.

La première requête v2 a rencontré une erreur native 401. Le journal de
l'application a confirmé un rafraîchissement du jeton postérieur à l'erreur.
Une reprise contrôlée du même UUID a récupéré les dix lectures. Le relais
automatise maintenant cette réparation uniquement après un tel événement
observé, avec tentatives bornées et sans lecture/export de secrets. Les tests
vérifient qu'un rafraîchissement antérieur à l'erreur n'autorise pas une reprise.

## Critères encore non atteints

CER nul, couverture totale, absence de refus, géométrie des quatre bords/mots
sur références réelles, OLR mesurée sur AS, illustrations et séparateurs,
validation de toutes les pages réservées. Le succès fonctionnel d'un export
ne remplace pas ces mesures. La prochaine boucle doit partir des erreurs
mesurées, conserver la sélection et publier les échecs restants.

## Cycle 4 : essais terminés et défaut géométrique observé

Gemini 3.1 Pro High est maintenant sélectionné dans le terminal existant,
avec preuve native sauvegardée. Les planchettes v4 conservent les pixels natifs.
Sur OCR17, la lecture conditionnelle fait 18/489 erreurs strictes et 7/489
conventionnelles, comme le compte v1 mais avec des erreurs différentes.
L’export refuse encore L0012 : CER strict 45/489 (9,20245 %), conventionnel
34/489 (6,95297 %), couverture 94,47853 %. Les règles de transcription
sont dans TRANSCRIPTION.md, déclarées avant cet essai ; les marques brutes de
césure restent enregistrées et notées aussi. Le protocole d’évaluation v1
et son empreinte sont inchangés. Ce résultat ne démontre pas le CER nul.

Les cinq pages de segmentation ont été traitées entièrement :

| Page | Prédictions / références | F1 IoU 0,75 initial | F1 IoU 0,75 encre | Omissions IoU 0,50 encre |
|---|---:|---:|---:|---:|
| La Fronde | 1007 / 960 | 0,76462 | 0,93747 | 16 |
| Le Matin | 1200 / 1140 | 0,43846 | 0,72650 | 50 |
| La Presse | 910 / 912 | 0,68496 | 0,79254 | 52 |
| L’Œuvre | 602 / 363 | 0,33782 | 0,60933 | 13 |
| OCR17 | 19 / 19 | 1 | 1 | 0 |

Toutes les détections sont conservées, y compris celles sans correspondance.
Un cache atomique par tuile rend désormais les longues inférences reprenables ;
un test interrompt la deuxième tuile et vérifie la réutilisation de la première.

Une vérification sur l’encre montre que les anciennes moyennes de pics CTC
coupent des glyphes. L’esperluette de L0012 était découpée entre deux mots
voisins. La nouvelle frontière doit traverser une colonne blanche observée
entre les caractères adjacents. Le rejeu des 19 lignes conserve 19 placements
et 78 frontières blanches. Cela corrige un défaut mesuré, sans certification
de mots : OCR17 n’a pas de référence de mots exploitable, et huit intervalles
de caractères anciens débordent encore de l’enveloppe d’encre du mot.

Les échecs d’essais sont conservés : segmentation par composantes natives
(F1 0,25955 à IoU 0,50 sur L’Œuvre), première correction automatique des espaces
(environ 100 insertions), et relecture de glyphes ancrée sur l’hypothèse
(CER conventionnel 7 → 9 erreurs). La seconde proposition d’espacement corrige
deux écarts, mais reste un diagnostic nécessitant réalignement. Une relecture
avec cible masquée est en cours. Aucun de ces essais n’est présenté comme une
validation de la chaîne entière. L’objectif reste actif.

## Cycle 5 : mots, caractères, reprise et pages denses

La vérification indépendante de géométrie reprend les **12 lignes fixes**
du pilote avec boîtes PAGE : elle demeure un diagnostic séparé, pas une
certification de segmentation/OLR. Les variantes et leurs refus sont conservés.
Les fragments de plis en haut et d’une ligne voisine en bas peuvent remplir
les blancs ; une variante les sépare à partir du contraste par composante
et d’une estimation locale de ligne de base, sans référence.

| Page diagnostic | Mots appariés / références | IoU médian initial → local | p99 des 4 bords, caractères initial → local |
|---|---:|---:|---:|
| La Fronde | 24 / 28 | 0,95387 → 0,96390 | 0,27784 → 0,12422 |
| Le Matin | 21 / 24 | 0,81340 → 0,82737 | 1,58218 → 0,75890 |
| La Presse | 22 / 26 | 0,75346 → 0,79997 | 1,19559 → 0,78499 |

La couverture lexicale reste inférieure à 100 %, et La Presse reste sous
0,80 d’IoU médian. Les lectures incertaines sont signalées. La variante brute
refusait deux lignes de La Presse ; le masque global en refuse encore une,
le masque local n’en refuse aucune sur ces 12 cas. Rien n’est arrondi vers
un seuil de réussite et aucune ligne difficile n’est retirée du bilan.

Sur OCR17, le réalignement CTC dans chaque recadrage de mot conserve
19 placements et 488 positions pour le texte NFC produit. Tous les intervalles
non blancs restent dans leur mot. Les espaces portent un intervalle blanc
observé et une confiance CTC inconnue (= 0), avec source déclarée. Les deux
corrections d’espacement donnent 5/489 erreurs conventionnelles conditionnelles
(1,02249 %), 16/489 strictes (3,27198 %). Le refus de coût typographique de
L0012 est conservé : l’export fait 32/489 erreurs conventionnelles (6,54397 %),
43/489 strictes (8,79346 %), couverture 94,47853 %.

Le nouvel export passe les XSD et les lecteurs réels : 18 lignes PAGE/ALTO
Kraken, textes/IDs/ordre exacts ; IR Axel entièrement identique après
sérialisation et lecture, 461 positions exportées. Le contrôle complet a
révélé que le dictionnaire de provenance des articles devenait une chaîne
Python dans Axel ; BBVLM émet désormais une chaîne JSON, conformément au
contrat de provenance `dict[str,str]`. Les anciens contrôles d’exactitude
portaient sur les lignes et positions, pas sur tout ce dictionnaire.

Une vérification aveugle des mots refusés par le coût de police est implémentée
mais son essai natif reste à faire. Elle ne transmet ni le texte attendu ni
une référence à Gemini : tous les recadrages de mots doivent être lus exactement
et sans incertitude, après contrôle des frontières et positions. Le coût
historique et le statut précédent restent visibles. Aucun refus n’a été
levé sans cet essai. La relecture de 26 glyphes avec cible masquée n’a produit
aucun changement ; elle n’est pas adoptée comme correction.

La production entière des cinq pages dev est en cours, sans limite de lignes.
La Fronde compte 1007 détections automatiques. La segmentation des 16 pages
réservées est aussi lancée, avec cache par tuile. Les commandes, jobs et UUID
sont dans CONTINUATION.json cycle 5 ; les compteurs évoluent dans les journaux.
Pour les pages de plus de 128 lignes, la nouvelle passe OLR compacte les
sorties par groupes géométriques. Gemini peut grouper/scinder/ordonner par
IDs ; l’expansion vérifie ensuite chaque ligne et les références d’articles.
Le contrat a été testé sur 1000 lignes, mais ses scores natifs AS manquent encore.

Une interruption contrôlée a récupéré la requête native déjà envoyée et
réutilisé 64 lectures avant la suite, sans renvoi du même job. Un parent de
32 lignes avait échoué à la récupération de format et avait été relu en
16+16. Ses deux réponses enfants ont été vérifiées, y compris les SHA des
crops natifs identiques, avant de rendre son rejet durable ; aucune réponse
Gemini originale n’a été inventée. Désormais un échec de récupération après
format natif terminé est mis en cache, même si l’historique disparaît.

57 tests passent. L’objectif demeure actif : CER nul, couverture intégrale,
ALTO/OLR mesurées et pages réservées ne sont pas encore démontrés.


## Cycle 6 — Recadrages incomplets et reprise du placement

La mesure intermédiaire de768 lectures de La Fronde apparie711 lignes,
soit26134 caractères :660 différences strictes et315 conventionnelles.
57 lectures sans correspondance ajoutent805 caractères. C’est un diagnostic
conditionnel incomplet, avant tous les refus et l’ordre OLR. Plusieurs erreurs
importantes viennent de débuts/fin de lignes tronqués par BLLA et de deux
colonnes mêlées dans un recadrage. Les pixels ont été inspectés ; aucune
référence n’a été envoyée au lecteur ni à la réparation.

L’extension naïve vers les régions PP régresse sur La Fronde : F1 IoU0,50
0,959837→0,932384. Une seconde variante exige une continuité de composantes
natives sur la même ligne de base et un blanc borné, avec tous les IDs gardés.
Les cinq pages dev sont mesurées, toutes lignes conservées :

| Page | F1 IoU0,75 encre | F1 IoU0,75 extension bornée |
|---|---:|---:|
| La Fronde |0,937468|0,947636|
| Le Matin |0,726496|0,705128|
| La Presse |0,792536|0,788145|
| L’Œuvre |0,609326|0,609326|
| OCR17 |1,000000|1,000000|

La seconde variante **n’est pas promue** : elle régresse sur deux familles.
À IoU0,50, Le Matin perd un appariement ; L’Œuvre en gagne un. Les sources,
paramètres, boîtes précédentes et scores restent dans dev-line-repair-v2.
La certification complète exige encore de réparer les omissions, les lignes
intercolonnes et les fragments voisins, puis de noter les lectures correspondantes.

Un incident natif a demandé Bash pour consulter un journal interne après
perte du prompt courant. Cette commande a été annulée ; après le retour natif
done, le même UUID a repris uniquement les images autorisées et fourni ses32
lignes. Le relais automatise cette annulation/reprise bornée, avec preuve,
sans contrôler une UI inconnue et sans renvoi après timeout ambigu.

Le placement dispose maintenant d’un cache atomique par ligne terminée,
lié aux pixels, boîtes, lectures, modèles et code. Le test injecte un arrêt
après un placement : celui-ci est réutilisé, le placement interrompu est
recalculé, puis les collisions globales sont de nouveau vérifiées. La première
page dense a été reprise sous la même requête native pour activer ce cache
avant ses1007 placements. Une réparation OLR identifiée et terminée peut
également être reformattée une fois ; les intentions ambiguës restent conservées.

64tests passent. Le traitement de la première page dense est en cours, puis
son export sera noté indépendamment. Les quatre autres dev et les seize pages
réservées restent dans la suite et le verdict. L’objectif reste actif.


## Cycle 7 : page dense, refus et premier diagnostic OLR AS

La Fronde entière termine ses 1007 lectures automatiques, son alignement et son
export. Le résultat échoue largement aux critères gelés : 451 lignes retenues,
546 refus pour superpositions inter-lignes, 8 lectures non résolues, un échec
CTC et un coût de police suspect. Le CER exporté est de 21187/34159 (62,02465 %)
selon la convention v1, 21378/34161 (62,58014 %) en NFC strict ; la couverture
est de 39,78454 %. La lecture conditionnelle des lignes appariées est à
1,16344 % conventionnel, mais elle omet les pertes de détection et les refus.

Les 1919 mots exactement appariés représentent seulement 31,85062 % des 6025
mots de référence. Leur IoU médiane de 0,95833 et leurs petits écarts de bords
ne compensent pas cette couverture. Le schéma ALTO 4.4 et les vrais lecteurs
Kraken PAGE/ALTO et IR Axel acceptent les 451 lignes, avec texte/IDs/ordre
exacts et 13856 positions. Ce contrôle établit la compatibilité, pas la qualité.

La réponse OLR native dépassait la capture de 1000 lignes du terminal. Le
format `bb-olr-tuples-v1` supprime les propriétés répétées sans supprimer les
contraintes. Une réparation native terminée avait deux blocs identiques
répétés, dupliquant cinq lignes ; un second tour de contrat a été autorisé
uniquement après réponse compacte complète identifiée et preuve de fin native.
Chaque tour conserve UUID, état, hash et réponse brute. Aucun timeout ambigu
n'est renvoyé. L'OLR obtenue comporte 284 blocs textuels, 94 séparateurs et un
article unique ; aucune qualité sémantique n'est certifiée sur cette page sans
référence typée.

Un défaut de construction des groupes physiques divisait x par la hauteur de
chaque ligne, ce qui changeait les colonnes aux changements de corps. Les
composantes physiques sont maintenant distinctes des séquences d'ordre déclaré.
La Fronde passe de 275 à 255 groupes, avec tous les IDs conservés. Le diagnostic
AS initial utilise 228 groupes et 870 lignes intégralement automatiques : aucune
VT, région humaine ou boîte de mot humaine ne lui est fournie. Il évaluera
seulement types, ordre et articles, jamais la chaîne complète. Les mesures
strictes OLR ont été ajoutées avant son premier résultat : appariement non typé
à IoU 0,50, classification exacte ensuite, incertitude non créditée ; les
séparateurs ont un score séparé et ne gonflent pas le F1 des blocs textuels.

Le rejeu du masque limité aux polygones du détecteur garde 561 lignes au lieu
de 451 : couverture des caractères 51,42715 %, couverture des mots 41,70954 %,
CER conventionnel 50,72455 %. Il reste 436 refus de superposition et la variante
n'est pas promue. Les transcriptions et anciens caractères CTC n'ont pas été
modifiés ; ce rejeu n'est pas certifié pour l'entraînement.

L'audit des masques observe 486 intersections de rectangles, dont 322 sans
pixel commun dans les deux masques et 164 avec encre partagée. Ces masques
restent imparfaits. Un audit privé séparé trouve 500 intersections entre
rectangles de mots de lignes différentes dans la référence humaine, touchant
478 lignes. La fidélité aux rectangles natifs et l'absence totale de croisements
rectangulaires sont donc en tension sur cette page. Le critère gelé reste en
échec ; aucun glyphe n'est rogné et aucun refus supprimé pour obtenir un succès.

La vérification aveugle native des cinq mots de la ligne OCR17 L0012 confirme
leur lecture, sans aucun texte attendu dans les entrées Gemini. L'export
`dev/ocr17-blind-word-export` conserve désormais 19/19 lignes, sans refus :
CER conventionnel 5/489 (1,02249 %), strict 16/489 (3,27198 %), couverture 100 %.
Les lecteurs réels retrouvent les 19 lignes et 488 positions exactes. Il reste
cinq erreurs conventionnelles et aucune référence humaine de mots sur cette
page ; aucune perfection n'est annoncée.

Les 16 segmentations réservées sont terminées et notées pour la première fois.
Leurs F1 à IoU 0,50 après rétraction encre vont de 0 à 0,98292 : BNL reste à
0,31373 et 0 ; le deuxième Matin à 0,54683 ; les quatre AS à 0,85514, 0,98292,
0,94337 et 0,96484. Tous les cas restent dans le verdict. Ces pages sont
maintenant connues pour la segmentation, et leurs VT/OLR complètes manquent.

70 tests passent. Le protocole et la convention demeurent inchangés. L'objectif
persistant reste actif : poursuivre l'attribution de l'encre, la segmentation
difficile, la compréhension OLR native et toute la suite fixe, sans humain.


## Cycle 8 : unités physiques, échelle du détecteur et refus OLR

Les premiers scores BNL du cycle 7 sont invalides pour la géométrie : leurs
ALTO déclarent `mm10` et le chargeur les traitait comme des pixels. Les anciens
rapports sont conservés. COORDONNEES-EVALUATION.md déclare la correction avant
les nouvelles mesures : DPI300 documenté par la BNL, facteur300/254 prescrit par
ALTO, appliqué aux lignes et mots, sans ajustement sur les scores. Les unités
physiques sans DPI explicite sont désormais refusées. Le banc historique a
la même correction ; son ancienne exclusion BNL par encre dans les blancs
n'est pas probante. Aucun seuil ni convention textuelle n'est modifié.

Le défaut du détecteur sur une bande courte est distinct : son estimation
excluait les grands corps dépassant5% de la hauteur du document, conservant
surtout des points ; le redimensionnement pouvait ensuite agrandir les vrais
glyphes excessivement. La stratégie explicite `auto-v2` estime le corps pondéré
par l'aire d'encre pour les canevas de hauteur inférieure1800, avec cible20pixels
réseau. Les grandes pages gardent le détecteur précédent. Les21pages fixes sont
comparées, avec anciens et nouveaux BNL tous deux convertis correctement :

| Page BNL | Détection IoU0,50 ancienne/nouvelle | IoU0,75 ancienne/nouvelle | Couverture lignes nouvelle |
|---|---:|---:|---:|
| 0000 |0,78431 /0,93333|0,47059 /0,88889|21/22,23propositions|
| 0001 |0 /1|0 /1|5/5,5propositions|

Les19autres pages ne régressent pas. Les sorties achevées sont réutilisées
quand la nouvelle branche est inactive ; aucune inférence achevée n'est requise
à nouveau. La clé des checkpoints inclut la hauteur réseau expérimentale.
`--segmentation-from` transmet au driver les sorties automatiques déjà terminées,
avec mêmeimage/configuration/version et rejet des champs de référence.

Le diagnostic natif AS OLRseul termine après annulation d'une demande de journal
interne, reprise bornée du mêmeUUID et sauvegarde du retour JSON. Il échoue :
232blocs,232incertains, aucunarticle, F1détection0,77155, classification0,
Kendall0,23256, couverture des847lignes de référence86,42267%, séparateurs et
illustrations F1=0. La passe suivante doit donner des recadrages locaux natifs
pour la compréhension et disposer des VT complètes ; ce diagnostic sans VT ne
certifie aucune chaîne complète.

Le score d'articles Axel sur l'intersection vide des IDs donnaitF1=1 malgré
zéroappartenance résolue. Le score primaire BBVLM compte désormais toutes les
51504paires d'articles des847lignes de référence : ce résultat estF1=0,
couverture0. Les lignes manquantes réduisent le rappel, les IDs supplémentaires
regroupés ajoutent des fauxpositifs ; les appartenances incertaines ne sont pas
créditées. Aucun fichier Axel n'est modifié.

Après sauvegarde et clôture de toutes les requêtes natives, la commande `/clear`
documentée dans l'aide native ouvre une nouvelle conversation dans le même
terminal Gemini3.1ProHigh. Le driver des5dev reprend : Fronde réutilisée, les
4autres pages en cours, avec exclusivité du canal Gemini et checkpoints par
requête/placement. Les16chaînes réservées complètes restent à produire.

76tests passent. L'objectif reste actif. Les refus de rectangles/encre, les
cinq erreurs conventionnelles OCR17 et toutes les pages manquantes demeurent
dans le verdict. La compatibilité des lecteurs ne prouve pas la fidélité des
positions de caractères ; cet axe demande un audit supplémentaire.


## Cycle 9 : positions de ponctuation et incident réseau

L’audit des 488 positions OCR17 découvre deux intervalles non blancs de largeur
nulle, malgré des supports CTC supérieurs à 0,98. Ils correspondent aux virgules
de « cher, » et « voſtre, ». Le rejeu expérimental choisit une composante native
dominante dans chaque mot, avec séparation du caractère précédent ; les
composantes concurrentes ambiguës restent non résolues. Les nouveaux intervalles
sont [2098,2147) et [1853,1911), avec confiance CTC inconnue (=0). Les anciens
intervalles/probabilités, pixels, candidats et sources sont conservés. Ni texte,
ni boîtes de mots, ni éligibilité ne changent. Cette variante n’est pas promue
au producteur et n’a pas de référence indépendante de glyphes.

L’export isolé `dev/ocr17-native-punctuation-export` conserve 19/19 lignes et
488 positions, valide PAGE/ALTO et passe les vrais lecteurs Kraken/Axel avec
textes, IDs, ordre, offsets et IR exacts. L’inspection des crops confirme les
composantes de virgules. CER conventionnel toujours5/489, strict16/489,
couverture100%, aucune perfection. La provenance des réparations est conservée
dans annotations et JSONL ; compatibilité ne signifie pas certification.

Le driver Matin s’est arrêté après plusieurs erreurs réseau natives, avec
224 lectures validées en cache. Une soumission à huit lignes sans activité
observée est reprise de manière bornée avec le même UUID, après capture de
l’état natif terminé et de l’erreur. Gemini travaille à cette reprise ; aucune
requête ambiguë n’est envoyée en parallèle. Les preuves et la commande exacte
sont dans CONTINUATION.json. 78 tests passent ; l’objectif persistant reste actif.


## Cycle 10 : reprise effective et compréhension OLR locale

La reprise réseau identifiée a terminé : les huit lignes L0225–L0232 ont été
validées et enregistrées sous leur UUID d’origine. Le driver repart depuis
ses caches et atteint 256 lectures Matin validées au checkpoint, sur 1200
lignes automatiques. Aucun résultat perdu n’est fabriqué et aucun agent
supplémentaire n’est créé. Les autres pages restent requises.

Le défaut OLR précédent conduit à une nouvelle voie locale. Les vues conservent
chaque pixel natif, avec IDs dans une marge extérieure, parties chevauchantes
et coordonnées automatiques originales inchangées, y compris les flottants PP.
L’audit réel AS1 couvre tous les rectangles de 228 groupes et 48 candidats
avec 319 vues exactes. Ce contrôle porte sur le transport visuel, pas sur la
qualité OLR. Un premier essai révélant les coordonnées flottantes a été corrigé
par floor/ceil uniquement pour le recadrage, sans modifier les propositions.

La voie locale prépare 35 lots couvrant toutes les lignes et tous les candidats.
Gemini doit donner frontières, types et ordre locaux, avec notes visuelles
courtes par IDs ; ces notes ne sont pas des VT. Les articles sont explicitement
hors de cette seule étape locale et ne provoquent pas d’incertitude artificielle
de type. Une passe globale séparée reste obligatoire pour réconcilier blocs,
ordre et articles sur toute la page ; les coupures de lots ne sont pas des
frontières d’articles. La reprise sauvegarde chaque UUID local, et la clé globale
inclut toutes les propositions locales. Aucun attendu humain n’est fourni.

La préparation est terminée ; aucune requête native locale n’est encore soumise,
car Gemini reste réservé au driver des pages dev. Les 232 blocs incertains et le
F1 articles nul du diagnostic précédent restent dans le verdict. 83 tests
passent. Critères et convention inchangés, objectif persistant actif.


## Cycle 11 : copies physiques, encre conservée et essai d’échelle

Le diagnostic de copies physiques demande texte de production compatible,
ancres CTC proches sur une même ligne physique et au moins98% d’encre partagée.
Le premier essai à masques locaux accepte zéro copie : les seuils adaptatifs et
les filtres locaux varient avec le recadrage. Une observation globale commune,
limitée à la cellule source du mot identifié, confirme deux fragments de La
Fronde. La conservation d’encre élargit le mot canonique du i de4pixels vers
le haut et le bord du e. de1pixel. Les anciens rectangles/positions et décisions
restent sauvegardés ; tous les1007IDs/textes sont conservés. Les images natives
confirment qu’il s’agit du i de « qui » et de la fin de « troisième. ».

Le bénéfice ne doit pas être surestimé : les lignes canoniques gardent d’autres
collisions. Rectangle : toujours451 retenues,544collisions+2copies ; polygonal :
toujours561,434collisions+2copies. CER conventionnels inchangés62,02465% et
50,72455%, couvertures caractères39,78454% et51,42715%. Aucun seuil final ne change
et la variante n’est pas promue. Les caractères de ligne restent non certifiés.

Une nouvelle comparaison d’échelle vise toutes les21pages fixes avec la même
estimation d’encre et cible20pixels déjà testées sur BNL. Les grandes images
équivaudraient à des canevas réseau de5333–6857pixels de haut ; la machine a
16GiB de RAM. Le routage expérimental borne le canevas par tuiles recouvrantes,
avec source complète couverte et cache exact par image/modèle/tuile/hauteur.
Les pages petites compatibles gardent la passe globale. Les paramètres,
projections effectives et plans de toutes les pages sont sauvegardés avant
mesure. Les anciennes sorties BNL sont réutilisées par leurs caches vérifiés.

L’inférence21pages est en cours. Les avertissements du polygoniseur sont
conservés dans le log ; la notation indépendante devra compter toutes les
omissions et régressions, avec unités BNL converties à DPI300 documenté. Aucun
succès n’est attribué à cette variante avant les scores. Le driver Matin atteint
832lectures validées au checkpoint et reste seul utilisateur de Gemini.
88tests passent, objectif persistant actif, aucune perfection acquise.

## Cycle 12 : lecture Matin, quota natif et régressions d’échelle

Les1200lectures initiales du Matin sont validées, dont36incertaines. La notation
indépendante, sur segmentation automatique et lecture seules, donne2879/37990
erreurs conventionnelles(7,57831%) et3134/37990strictes(8,24954%). Elle compte
les refus/omissions et1556caractères supplémentaires sans correspondance ;
couverture des caractères97,11503%. Le CER conditionnel sur lignes appariées
est0,61528% conventionnel,1,30645% strict, diagnostic qui ne remplace pas le CER
complet. La géométrie et l’OLR finales restent à mesurer.

Le terminal annonce un quota individuel, avec remise à zéro explicite. Le driver
est arrêté, les69requêtes concernées identifiées par UUID/erreur native et68
placements intermédiaires mis en quarantaine réversible. Les1200lectures
initiales, images, requêtes, rejets et preuves sont conservés. Un incident de
service n’est pas certifié comme une ligne illisible. La nouvelle garde partagée
empêche toute demande de lecture/format/OLR pendant le quota ; le driver attend
l’échéance persistée, puis doit récupérer le mêmeUUID après preuve Done, une
seule fois par erreur de quota.98tests passent, dont délai/fin native, absence
de renvoi sur timeout, cache disponible pendant quota et quarantaine ciblée.
L’attente réelle est entrée ; la reprise native après reset reste à démontrer.

Les cinq pages dev de l’essai d’échelle sont mesurées sur la même suite/protocole.
Les rectangles d’encre évoluent ainsi :

| page | F1 IoU0,50 baseline → échelle | F1 IoU0,75 baseline → échelle |
|---|---|---|
| Fronde |0,95984 →0,96383|0,93747 →0,91900|
| Matin |0,93162 →0,93293|0,72650 →0,70995|
| Presse |0,94402 →0,94240|0,79254 →0,77235|
| Œuvre |0,72539 →0,73827|0,60933 →0,51721|
| OCR17 |1 →1|1 →1|

La variante n’est pas promue. Un complément conservateur garde exactement les
rectangles primaires et n’ajoute qu’une détection non doublonnée avec90% d’encre
native nouvelle. Tous les candidats restent dans l’audit. Il ajoute5lignes
Fronde,2Matin,14Œuvre mais dégrade leursF1 ; Presse/OCR17 restent identiques.
Il n’est pas promu non plus. Les seize réservées de l’essai d’échelle continuent,
avec avertissements du polygoniseur et omissions comptés dans la comparaison.
Critères/conventions inchangés, objectif persistant actif, aucun fichier Axel
modifié. Les échecs Fronde/AS/OCR17 et toutes les chaînes réservées manquantes
restent dans le verdict.

## Cycle 13 : ponctuation native entière et défaut d’encre entre lignes

Le snapshot Matin contient1128placements locaux sur1200 ;69sont en réparation
de quota et3encore non calculés. Il a17intervalles non blancs nuls malgré une
portée CTC au mot. L’observation native montre des signes terminaux coupés par
le rectangle du mot. La première réparation locale a aussi crédité un point
de la ligne voisine à « Nathan. » ; cet essai est réfuté pour ce caractère.
Un point après35était seulement un fragment coupé au bord du rectangle.

La variante corrigée utilise un contexte natif plus large, une binarisation
relative à la taille du mot, des composantes entières ne touchant pas les bords
du recadrage, une position verticale cohérente pour point/virgule et des traits
horizontaux isolés pour la césure. Les textes/IDs/éligibilités ne changent pas.
Les anciens rectangles, intervalles/probabilités CTC et blancs restent dans la
provenance ; la confiance des positions natives est inconnue(0). Aucun attendu
ni boîte de référence ne sert à choisir les composantes.

L’essai v7 répare13/17intervalles, conserve4nonrésolus et modifie12mots. Dix
sont comparables indépendamment :9IoU améliorés,1régressé. La couverture ne
progresse pas : le filtre global appliqué au seul snapshot conserve209lignes
et refuse916collisions, avant/après identiques. Ce résultat incomplet ne devient
pas un verdict de page entière. Les mots englobent encore l’encre de la ligne
voisine ; l’attribution d’encre aux lignes reste le prochain problème principal.

L’export OCR17 isolé répare les2virgules, garde tous les mots/textes/statuts et
19/19lignes,488positions. PAGE/ALTO valides, vrais lecteurs Kraken/Axel exacts,
IR aller-retour exact. CER inchangé5/489conventionnel(1,02249%) et16/489strict
(3,27198%), couverture100%. L’absence de référence indépendante de glyphes
interdit la certification de leurs positions.109tests passent. Aucun essai n’est
promu, aucun seuil/convention relâché ; quota principal en attente persistante,
échelle21pages en cours, objectif persistant actif et fichiers Axel intacts.

## Cycle 14 : attribution native de l’encre et reprise après quota

Le masque fondé sur des composantes entières et les baselines BLLA automatiques
n’utilise aucun texte ni polygone humain. Son remplacement complet du masque
régresse :308lignes retenues,241avec extension aux composantes complètes,
contre451actuellement. Tous1007IDs, refus et composantes nonattribuées restent
comptés. Ces essais historiques sont conservés.

Le filtre conservateur enlève une composante locale entière seulement si95%
de ses pixels coïncident avec des composantes natives attribuées à un seul autre
ID. Les premières versions faisaient suivre huit ponctuations à une lettre de
la ligne suivante ; les huitcas ont été inspectés sur les pixels. Les marques
proches de leur baseline et les traits horizontaux gardent désormais leur ID.
Le nouveau filtre donne521retenues,476collisions,8lectures nonrésolues,
1alignement nonrésolu et1coût suspect. Aucun refus supplémentaire de masque.
Les textes et positions CTC restent exactement identiques.

| Mesure indépendante de La Fronde | Actuel | Filtre expérimental |
|---|---:|---:|
| Couverture caractères |39,78%|47,09%|
| CER conventionnel, omissions comprises |62,02%|54,76%|
| CER strict NFC |62,58%|55,40%|
| Couverture mots |31,85%|37,89%|
| IoU médiane des mots mesurables |0,95833|0,95711|
| Bord extrême en pixels |33|33|
| Bord extrême en caractères |0,98755|0,94186|

Le diagnostic de boîtes de lignes est aussi mesuré sur les cinqpages fixes,
sans VT ni export certifié. ÀIoU0,75, leF1 passe de0,72650à0,84957surMatin,
0,79254à0,85291surPresse,0,60933à0,70259surŒuvre, mais régresse de0,93747à
0,92832surFronde. OCR17resteà1. LeF1 àIoU0,5 régresse aussi surFronde/Presse.
Les baselines verticales restent explicitement nonrésolues avec leur détection
originale ; aucun faux tracé n’est inventé. Tous16réservés sont programmés.
Variantes nonpromues,120tests passent, critères/convention inchangés.

L’attente de quota a réellement expiré et le driver reprend les UUID existants
après preuve nativeDone, une fois par erreur. Les réponses validées sont
sauvegardées par BBVLM. Un libellé de fournisseurGoogle sous modèle/footerGemini
révèle un défaut du contrat exact ; sa preuve et son rejet sont conservés pour
une réparation mécanique de provenance, sans changement de transcription.

## Cycle 15 : provenance native et bilan réservé du masque

Une réponse native de L0044 portait le fournisseur Google, avec modèle déclaré
et footer Gemini 3.1 Pro. Le contrat exact avait rejeté cette étiquette et produit
un refus vide de fournisseur inconnu. La normalisation est désormais limitée à
ce nom de vendeur, avec UUID exact, modèle Gemini et footer natif après la
réponse, sans UUID ultérieur. Le nom original, le modèle déclaré, le footer et
la preuve sont conservés ; le texte ne change pas. Une autre famille ou une
preuve absente interrompt le relais au lieu de fabriquer un refus OCR.

Le cas réel est réparé depuis son terminal sauvegardé avec zéro appel natif.
Rejet, état et réponse originaux restent accessibles. Un seul placement
intermédiaire est mis en quarantaine réversible ; sa provenance est recalculée.
La ligne est un filet décoratif, toujours vide et incertaine : aucun gain de
transcription ou de couverture n’est attribué à cette correction.

Le rechargement du worker est effectué après clôture native de L0759. Son UUID
existant est récupéré par get/read, sans nouveau prompt, puis sauvegardé. Les
anciens workers sont terminés avant relance du driver depuis les mêmes caches.
127tests passent. Ce résultat démontre la récupération et la provenance, sans
certifier les erreurs de lecture ou de géométrie restantes.

Les16pages réservées du filtre d’encre sont maintenant toutes mesurées. LeF1
àIoU0,75 monte surMatin/Presse/Œuvre etAS1, mais baisse sur les deuxFronde,
BNL0000 etAS2/AS3/AS4. AS1passe de0,07710à0,37150 ; AS3de0,57250à0,42439.
Ces régressions et toutes les omissions restent dans le bilan. L’expérience
est non promue ; ce diagnostic ne produit ni VT, ni mots, ni OLR certifiés.
L’exposition de cette mesure géométrique réservée est documentée.
