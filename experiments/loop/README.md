# BBVLM — boucle expérimentale en cours

État au 27 septembre 2026 : **objectif global non atteint**. Boucle reprenable,
PERO exécuté sur CPU, modèles VLM réellement appelés par sous-agents, exports
ALTO/METS validés. Aucun résultat n'est certifié comme vérité terrain parfaite.

## Résultats mesurés

G01 : conserver l'alignement natif PERO, affiner la hauteur des mots à partir des
pixels. Douze configurations comparées sur 0253902-001 ; sélection figée avant
les pages 0401692-003 et 752234-003. Paramètres : vertical, Otsu, marge 0,
composantes >=2 pixels, contraction maximale 50 %.

| Expérience | Page 0401692-003 | Page 752234-003 |
|---|---:|---:|
| IoU moyenne native, lignes/textes fournis | 0,6112 | 0,5910 |
| IoU moyenne affinée, mêmes entrées | 0,6900 | 0,6516 |
| F1 texte exact + IoU >=0,5, PERO depuis image | 0,7217 | 0,6081 |
| F1 texte exact + IoU >=0,5, PERO + G01 | 0,7977 | 0,6741 |
| Mots dont l'IoU conditionnelle se dégrade | 361/5385 | 509/5898 |

Les 19 mots non appariés sur la deuxième page restent au dénominateur ; aucune
suppression pour améliorer le score. L'intervalle bootstrap par ligne confirme
le gain moyen **sur chaque page** ; il ne prouve pas une généralisation par titre,
période ou langue. Les défauts de hampes/accents et les régressions restent ouverts.

**Réserve majeure découverte après mesure :** certains textes de référence sont
manifestement erronés et les marges de boîtes variables. Voir REFERENCE_AUDIT.md.
Ces chiffres mesurent l'accord avec les annotations distribuées. Ils ne suffisent
pas à établir une supériorité sur des références fiables, ni une GT parfaite.

Audit aveugle A01 : 45 lignes tirées uniformément au hasard sur les trois pages
françaises annotées au mot, graine et identifiants figés avant lecture. Luna et
PERO sont tous deux plus proches l'un de l'autre que de la transcription
distribuée sur 24/45 lignes (53,3 %, IC Wilson 95 % [39,1 ; 67,1]). Cela reste un
signal de triage, pas une adjudication. Indépendamment du VLM, l'audit structurel
trouve 121 caractères de contrôle C1 et 60 lignes contenant des séquences UTF-8
valides décodées comme Latin-1. Les sources originales n'ont pas été modifiées.

Décomposition CEV/SpACER approximative, sur les trois pages (boîtes caractère
indisponibles) : erreur de parsing 0,52 %, 0,16 %, 0,17 %, contre erreur OCR
2,72 %, 1,67 %, 3,84 %. Sous cette référence bruitée, la priorité expérimentale
est donc la transcription et sa référence indépendante, sans abandonner les
métriques OLR/régions/mots.

Le second corpus *Spiritualist* a lui aussi échoué comme référence de boîtes au
mot : 87,68 % des 175 548 mots chevauchent le voisin d'au moins 25 % et 11,69 %
sortent de la ligne ; 0/49 XML valide directement au XSD ALTO 4.4 à cause de cinq
attributs custom. Le split 4 développement / 8 validation a néanmoins été figé
avant images. Texte, 425 SSU et ordre restent candidats après audit séparé.

Un import de développement met les boîtes fautives en quarantaine, conserve les
SSU comme unités sémantiques (pas comme articles), importe l'ordre et produit un
ALTO/METS valide. Sur une passe Luna aveugle, l'ordre connu est 15/15 paires
après réparation diagnostique d'un ID, mais la réponse brute échoue le contrat
d'ID, fusionne 6 SSU en 3 (F1 0,774) et n'obtient que 7/12 rôles. Aucun de ces
scores n'ouvre un gate.

A03 corrige le problème de transport : sur les pages gelées 0003 et 0008,
Luna renvoie en une passe les 42 jetons courts exactement une fois ; le binder
les relie ensuite aux IDs stables, sans aucune réparation. Mais le contenu échoue
aux seuils préenregistrés : ordre micro 86,28 %, rôles 71,43 %, F1 SSU 49,23 %.
La page 0003 est particulièrement difficile pour l'ordre (57,14 %). Les pages
sont consommées ; ce résultat négatif interdit de conclure qu'une passe globale
VLM produit déjà des articles/SSU fiables. Il localise le prochain travail sur
les conventions, relations partielles et abstentions, pas sur les identifiants.

A04 retire l'ordre colonnaire simple de la passe VLM. Un ordonnanceur géométrique
calibré uniquement sur les quatre pages développement atteint 378/378 paires sur
la page 0014 gelée, contre 79,1 % pour le tri global haut→bas, en moins d'une milliseconde
CPU et zéro passe VLM. Il produit directement les arêtes du graphe. La portée est
conditionnelle aux régions distribuées et la référence d'ordre reste provisoire :
aucun gate global n'est ouvert. Quatre régions hors ordre restent dans la proposition
brute et exigent un filtre de rôle avant promotion. La page 0014 est maintenant consommée.

A05 combine ce chemin CPU avec une seule passe Luna réservée aux rôles, à
l'éligibilité du flux et aux unités sémantiques sur la page gelée 0015. La
réponse brute couvre strictement les 22 jetons sans réparation. Le filtre réussit
19/19 régions utiles, sans contamination ; les rôles atteignent 20/22 et l'ordre
final 171/171 paires. Le gate reste fermé car le groupement fusionne trop :
précision/rappel/F1 par paires 0,647/0,917/0,759 (seuil F1 0,80), malgré un F1
B-cubed de 0,870. Ce résultat valide l'économie d'une passe d'ordre mais pas les
articles. La page 0015 est consommée et ne sera pas utilisée pour valider la
prochaine règle de séparation.

A06 sélectionne sur les quatre pages de développement une règle CPU où un
`HEADER` ouvre une unité, sauf chevauchement vertical de blocs de titre ; avec
les rôles de référence elle obtient un F1 de paires macro 1,000. Une seule passe
Luna rôle/filtre est ensuite évaluée sur 0029. Le JSON brut est valide, mais le
rappel d'éligibilité tombe à 0,696, l'accord de rôle à 0,630, le F1 SSU à 0,680
et le rappel d'ordre combiné à 0,474 : le gate échoue et 0029 est consommée.
L'audit postérieur révèle que cinq des dix désaccords de rôle sont des publicités
visuellement explicites que Luna appelle `ADVERT`, tandis que la source n'offre
que les rôles physiques `HEADER`/`TEXT` et les inclut dans l'ordre. Le score
reste inchangé ; ce défaut impose de séparer rôle physique, genre éditorial et
appartenance au flux avant A07.

A07 met effectivement ces axes à part. Sur 0039, Luna conserve 21/21 régions
utiles et l'ordre CPU atteint 210/210 : aucun genre ne peut plus supprimer un
bloc physique. Le genre est stocké comme proposition non scorée. Le gate échoue
encore car le modèle confond les blocs courts de titre et de corps : 15/24 rôles
physiques, F1 SSU 0,591. Une règle hauteur/page calibrée uniquement sur
développement atteint 0,969 de F1 macro ; A08 la testera sur 0044, jamais sur
0039 désormais consommée.

A08 valide la réduction de tâche sur 0044 : une passe Luna grossière retrouve
10/10 régions du flux et la règle hauteur figée obtient 13/13 rôles physiques
et les quatre SSU exactement (F1 1,000). Le gate reste fermé : l'ordonnanceur
A04 ne découvre que deux colonnes au lieu des trois visibles et obtient 38/45
paires (0,844). 0044 est consommée ; A09 doit corriger les colonnes sur
développement avant toute utilisation de 0050.

A09 corrige l'ordre sur développement avec des ancres d'au moins 2 % de la
largeur et une affectation par recouvrement horizontal. Sur 0050, l'ordre passe
à 36/36, le flux à 9/9 et les rôles à 11/12. Le gate échoue encore : un grand
titre multi-ligne de 238 px est classé TEXT et fusionne deux unités (F1 SSU
0,733). Le split initial de huit validations est désormais entièrement consommé.

A10 remplace la hauteur du bloc entier par trois signaux internes : au plus deux
lignes, hauteur médiane de ligne/page ≥ 0,014 ou proportion de capitales ≥ 0,60.
Les seuils ont été choisis sur huit nouvelles pages développement seulement
(180 configurations, F1 SSU macro 0,958 ; rôles 0,989). Sur la première page
gelée 0004, conditionnellement aux régions et au flux grossier distribués, la
règle obtient 8/8 rôles, F1 SSU 1,000 et ordre 1,000, sans VLM. C'est un résultat
positif concret pour le défaut multi-ligne, mais pas encore un test end-to-end :
0004 est consommée et 0010 est réservée à la passe Luna grossière complète.

A11 exécute cette validation complète sur 0010 : Luna renvoie les 15 jetons une
fois chacun, sans réparation. Rappel du flux 11/11, précision 11/12, rôles
grossiers et fins 14/15, ordre 55/55, F1 SSU 0,857 ; tous les seuils gelés
passent. Le seul désaccord est une note éditoriale lisible que Luna conserve en
`STREAM/NOTICE` et que la source exclut comme `OTHER`. Le score n'est pas changé :
le bloc reste recherchable mais son appartenance au flux principal doit être
arbitrée. Ce succès reste conditionné aux régions distribuées et n'ouvre aucun
gate global.

DocLayout-YOLO a aussi été exécuté réellement sur 0044 : 2,36 s CPU, couverture
d'union 95,9 %, mais 25 prédictions pour 13 régions et rappel one-to-one IoU≥0,5
de 53,8 %. Il fournit des propositions utiles, pas des boîtes ALTO finales.

VLM : pilote allemand de 25 lignes / 916 caractères : Luna après reprise ciblée,
13 erreurs strictes ; escalade Sol sur 5 risques, 9 erreurs (2 après NFC + ſ→s).
Cela ne prouve pas une équivalence à un modèle frontier sur un corpus indépendant.

Pilote français : 24 lignes choisies au hasard parmi les détections PERO, 22
appariées à la référence / 878 caractères. CER strict distribué : PERO 5,13 %,
Luna 6,72 %, Luna + Sol sur 5 incertitudes 6,49 %. Deux lignes non appariées sont
listées séparément. Plusieurs pénalités proviennent de fautes de référence ou de
conventions d'apostrophes. Ne pas utiliser ce classement pour choisir le modèle
sans audit. La signature reste incertaine après Sol ; l'escalade n'est pas magique.

## Utilité documentaire déjà ajoutée

- Graphe typé : pages, régions, lignes, mots, articles, ordre, métadonnées,
  propositions et événements. Changement de texte => invalidation de l'alignement.
- Projections ALTO 4.4 / METS 1.12.1 validées par XSD hors réseau ; files de revue.
- Index lexical SQLite avec retour aux coordonnées, IDs ALTO et article proposé.
  Texte diplomatique conservé ; normalisation de recherche séparée. Zéro appel VLM.
- Réponses VLM strictement adressées par IDs, conservation des sorties brutes,
  des erreurs et des étapes de reprise. Aucun score synthétique étiqueté humain.

## Reprise

1. Lire CHECKPOINT.json, protocol.json, REFERENCE_AUDIT.md et LITERATURE.md.
2. Exécuter `python3 scripts/autonomous_loop.py --execute` pour les phases CPU
   manquantes. Ne pas exécuter simultanément deux pilotes sur le même état.
3. Consulter la littérature primaire avant une nouvelle hypothèse ; inscrire ce
   qui a été lu, son domaine, la limite d'extrapolation et le défaut visé.
4. Priorité : qualité des références et conventions ; obtenir une validation
   indépendante de textes/boîtes. *The Spiritualist* reste candidat pour texte
   et SSU/ordre, mais ses boîtes au mot sont rejetées ; utiliser ensuite
   OCR-D-GT-VD-SBB (livres historiques, contrôle annoncé élevé, mais domaine
   et langues différents). Ne pas transformer les prédictions de notre système
   en son propre jeu de test.
5. Mesurer la segmentation et le texte séparément. Tester les risques de crop
   tronqué avec contexte élargi. Un seul lecteur principal, escalade motivée.
6. Poursuivre OLR/articles, vocabulaire métadonnées, profil MODS/PREMIS,
   résolution des fichiers images, retrieval avec requêtes et jugements séparés.
7. Enregistrer résultats négatifs, coût disponible, hypothèse suivante et artefacts.
8. Après A12/A13, séparer explicitement contenu lisible/retrievable et flux principal,
   calibrer l'abstention sur développement seulement, puis tester une page
   encore intacte. Garder 0004 et 0010 consommées.

Pour sauvegarder un état portable : `python3 scripts/checkpoint_bundle.py`.
Le ZIP omet environnement, poids et archives de corpus, restaurables via
assets.json et restore_public_assets.py. Les sorties VLM et caches réutilisables
sont conservés. Le code n'a pas été poussé vers le dépôt distant.

## Conditions de réussite encore ouvertes

Audit des références ; gain de géométrie indépendant et diversifié ; couverture
end-to-end ; qualité OCR comparée à une référence frontier explicite ; exactitude
OLR/articles/métadonnées ; pertinence et fidélité des preuves de retrieval ; profil
documentaire complet et provenance. Les tests logiciels (46 réussis, 1 fixture
historique volumineuse ignorée dans le checkpoint portable)
vérifient des invariants, pas la perfection du contenu historique.

## A12 : colonnes YOLO, pas boîtes de mots

Les 25 détections déjà calculées sur 0044 donnent 3 colonnes et 45/45 relations
de rattachement correctes ; ce diagnostic explique pourquoi le précédent score
one-to-one au bloc ne suffisait pas. Le crop serré exclut une partie de 142/415
rectangles de lignes source ; les fenêtres avec contexte réduisent ce chiffre
à 3/415. Ce n'est ni une mesure d'encre perdue, ni une validation indépendante.
Les propositions et métriques se trouvent dans `spiritualist-v1/yolo-columns-a12-0044/`.

A13 enchaîne une vraie lecture Luna, puis une escalade Sol si non-exactitude,
sur trois petits crops YOLO sans référence fournie. Voir le rapport
`spiritualist-v1/yolo-ocr-a13-0044/report.json` et les réponses brutes.
Le choix de blocs courts n'est pas représentatif ; le routage par CER est un
diagnostic avec référence, pas une politique de production.

## A64 : CER normalisé HIPE, sans confusion avec le diplomatique

La projection figée des seize blocs A54 donne un micro-cMER HIPE de 0,6346 %
pour PERO, 0,3004 % pour Luna brut et 0,3947 % pour la sortie gardée. Luna brut
améliore 9 blocs, en égale 5 et en dégrade 2 ; 6/16 blocs sont exacts après la
normalisation officielle. Les 64 comptes H/S/D/I ont été vérifiés contre
jiwer. Cela répond à l'effet des tirets/ponctuation sans les effacer du texte
diplomatique : cette quatrième vue reste séparée de `strict_nfc_diplomatic`,
`search_v1` et `lexical_alnum`. Le résultat n'est pas 0 %, A54 est consommé et
les deux régressions exigent une adjudication image indépendante.

## A65 : frontières de crop sur 50 pages de validation
15 010 lignes valides mesurées, zéro modèle : 4 069 perdent >1% de leur
surface annotée sous masque du polygone parent, contre 2 222 sous rectangle.
La fusion de tous les polygones texte n'aide presque pas (4 061). En échange,
105/1 092 rectangles de régions capturent >1% de surface de régions voisines.
Ce diagnostic oracle ne mesure ni encre ni CER, et les polygones de lignes
ne sont pas parfaitement adjudiqués. Les 100 pages Test restent réservées.
Ne pas promouvoir les masques fins comme entrées OCR sans validation image.

Résultat A13 : 8/1 049 éditions pour Luna (0,7626 %), puis 7/1 049 pour Sol
(0,6673 %). Les différences sont ponctuation/espaces, pas des mots ; plusieurs
signes visibles manquent dans le XML. L'audit image de l'agent est sauvegardé
sans corriger la référence et sans certifier 0 % de CER. Une passe par lecteur,
trois crops par passe ; aucun nouvel appel au détecteur.

Attention : A10/A11 utilisaient aussi le texte et les lignes source dans les
règles typographiques. Même A11 `v6-full` n'est pas un test image seule.

## A14/A15 : colonnes → lignes → OCR → boîtes

A14 : détection PERO réelle (416 lignes, 8,30 s CPU, deux forwards adaptatifs)
réutilisée pour quatre assignations. Les colonnes imposées donnent 496 fragments,
ou 635 avec contexte recouvrant. Le rattachement entier conserve 416 lignes et
leurs polygones. Toutes variantes : 385/418 appariements IoU≥0,5. Le gain est
l'absence de fragmentation introduite, pas une supériorité sur PERO.

A15 : textes Sol A13, 20 lignes prédites, reconnaissance CTC en 3,32 s mise en
cache puis alignement sans nouveau VLM. Paquet partiel : 184 mots, ALTO/METS
valides, index de 20 passages ; 20 lignes à relire. IDs natifs restaurés par
contrat vérifié. Les overlays révèlent des tirets longs hors boîte : géométrie
parfaite non atteinte. Rapports dans `column-lines-a14-0044/` et
`predicted-alignment-a15-0044/` sous `spiritualist-v1/`.

Suite : ponctuation terminale et conservation d'encre sur développement, puis
validation diverse non consommée et référence adjudicable. Profil MODS/PREMIS,
fichiers image METS et retrieval indépendant restent ouverts.

A17 ferme une partie technique de ce point : sur le paquet partiel 0044, les
quatre groupes de fichiers et les doubles pointeurs image/ALTO sont résolus ;
trois checksums locaux sont recalculés, l'image distante est vérifiée avant
export et quatre objets PREMIS sont émis. Le gate reste fermé : MODS n'a pas
encore son XSD hors ligne ni une notice bibliographique indépendante, et cette
page est déjà consommée.

## A18/A19 : vrais nouveaux fichiers GT et ablation d'étages

`reference-a18/` contient une révision figée OCR-D/SBB : quatre ouvrages audités
(94 lignes, 623 mots), quatre ouvrages réservés sans téléchargement/inspection,
originaux, empreintes, crops aveugles, réponses brutes et panneaux d'audit.
Les boîtes source sont prometteuses, le texte niveau 3 exige une convention MUFI
explicite. Luna puis Sol ciblé ne modifient jamais la référence. Voir
`reference-a18/ocr-report.json` pour le CER strict et ses limites.

`gap-ablation-a19/` teste réellement une voie ne chargeant aucun réseau OCR :
50/94 lignes oracle SBB proposées, IoU émise 0,9453, mais rappel total 0,4575 et
neuf mots fortement mal positionnés ; 18/20 lignes prédites A15 proposées sans
GT mot valide. Rejet de la promotion automatique. La réserve reste intacte.
Priorité suivante : routeur de risque et conventions figés sur audit, CTC en
repli mesuré, puis validation réserve et presse française non-NewsEye. Le
contrat de lecture partagée et les ablations de coût/utilité sont décrits dans
`ARCHITECTURE_A19.md`. Tous les critères globaux restent non satisfaits.

## A20/A21 : conventions explicites et coût de la confiance

A20 sépare CER strict (13,01 % pour Luna+Sol ciblé), décomposition documentée
(6,11 %) et compatibilité SBB avec pertes (5,32 %), sur les mêmes 16 lignes.
Ce changement de métrique n'améliore aucune transcription. Les sources OCR-D
et le code dinglehopper épinglé sont conservés dans `conventions-a20/`.
A21 mesure en aveugle la relecture par Sol de toutes les six lignes que Luna
n'avait pas signalées : quatre comportaient encore des écarts. Résultat et
régressions éventuelles dans `routing-a21/report.json`. Ces expériences restent
diagnostiques ; la réserve SBB et les critères globaux sont inchangés.

A21 terminé : sur les six lignes reprises, trois améliorations et deux
régressions sous le profil décomposé ; au total CER 6,11 % → 5,16 %, mais
exactitude 3/16 → 2/16. Le remplacement automatique par Sol est rejeté.
CER strict final 11,88 %. Aucun texte composite choisi grâce à la GT.

## A22 : validation indépendante SBB consommée

Le protocole A22 a été gelé avant l'ouverture des quatre ouvrages réservés.
Une tâche Sol a réellement lu 16 cibles polygonales plus 16 contextes : CER
strict 11,62 %, CER décomposé 4,86 %, 3/16 lignes exactes. La réplication proche
d'A21 confirme que le niveau utile est autour de 5 %, pas 0 %.

Le localiseur sans reconnaisseur A19 émet 7 boîtes sur 2/16 lignes : toutes
IoU≥0,8, moyenne 0,971, mais rappel global 5,79 %. Sa couverture chute de
53,2 % en développement à 12,5 % sur réserve. Il reste un fast-path CPU avec
abstention ; CTC/PERO ciblé est nécessaire pour le reste. Voir
`reserve-a22/report.json`, le protocole et l'overlay complet des boîtes émises.
La réserve est maintenant consommée et ne peut plus être retunée/testée.

## A23/A24 : fallback CTC réel et résolution VLM

A23 exécute PERO 0.7.0 sur les 16 lignes A22 déjà consommées, layout désactivé.
Le coût mesuré est 1,81 s de reconnaissance CPU et 0,13 s d'alignement forcé.
Les 121 mots reçoivent une boîte, mais l'hybride A19/CTC-encre n'atteint que
19,83 % de rappel à IoU≥0,8 (IoU moyenne 0,636). Le post-traitement Otsu vu
après score monte à 91,74 % à IoU≥0,5, sans pouvoir servir de validation.

Sur le texte, PERO natif obtient 4,58 % de CER décomposé, contre 4,86 % pour
Sol A22. A24 relit les mêmes lignes avec page localisatrice, contexte 2x et crop
4x : 5,01 % décomposé et 12,22 % strict, donc légère régression. Ni résolution,
ni contexte élargi ne produisent le 0 % rapporté pour Claude/Gemini. Il faut
désormais un protocole commun nouvellement gelé, avec leurs sorties brutes et
la même convention Unicode, puis une validation indépendante.

## A25 : le resserrement Otsu gagne, la validation française échoue

Le candidat `ctc_raw_otsu_v1` a été décrit avant l'ouverture de quatre nouvelles
pages SBB : texte de référence aligné sur les logits CTC PERO, séparateurs aux
milieux, puis boîte serrée sur l'encre Otsu dans le rectangle de ligne. Sur 140
lignes et 1 097 mots, il couvre tout le vocabulaire et atteint 99,45 % de rappel
IoU≥0,5, 84,41 % à IoU≥0,8 et 0,9113 d'IoU moyen, contre 84,32 %, 16,77 % et
0,6541 pour les boîtes PERO natives. Reconnaissance CPU : 24,48 s ; alignement :
1,13 s. C'est le premier signal large montrant que les positions CTC servent
mieux de séparateurs que de boîtes finales.

Deux raisons interdisent la promotion : le script exact a été scellé après
l'ouverture, et l'ouvrage supposé français est en réalité majoritairement
allemand historique. Les lignes, le texte et l'ordre des tokens sont aussi
oracle. A25 est donc un diagnostic externe à risque, pas une validation
française ni end-to-end. Le détail est dans `french-holdout-a25/` ; la prochaine
réserve doit être multi-ouvrages, réellement française et scellée code compris.

## A26–A28 : GT séparées pour mots et OLR

A26 a téléchargé le lot officiel BnF IMPACT. Il est français et manuellement
transcrit, mais ses PAGE contiennent uniquement des régions : zéro ligne/mot.
Le gate vide de l'ancien évaluateur est rejeté. A27 réemploie donc ce lot pour
sa vraie force, les régions/classes/flux ordonnés. Sur une page scellée et 235
IDs opaques, Luna trouve exactement les 234 régions éditoriales mais s'abstient
sur le groupement en produisant 234 singletons : F1 de flux 0, contre 0,505 pour
la baseline géométrique avec rôles oracle. Une reprise Sol aveugle et ciblée est
enregistrée séparément : 34 flux, F1 0,591, ordre exact sur les paires couvertes,
contre F1 0,505 pour la baseline. Sol récupère exactement 7/13 groupes et
sur-segmente les six autres sans produire de fusion inter-groupe. Ce signal
justifie un futur mergeur CPU de continuations, mais A27 est consommée et
`OrderedGroup` n'est jamais appelé vérité d'article.

A28 est le premier test de boîtes réellement français, multi-ouvrages et scellé
avant ouverture : 8 pages, 261 lignes, 1 753 mots. CTC+Otsu domine PERO natif
(IoU≥0,5 93,44 % contre 68,91 % ; IoU≥0,8 68,45 % contre 11,07 %) mais échoue
au gate strict sur chaque page. PERO natif reste à 4,64 % de CER strict et
2,40 % décomposé. Les pires échecs montrent encre de ligne voisine et verso
translucide ; un Otsu par cellule n'apporte presque rien. La suite doit filtrer
les composantes par bande de baseline puis valider sur une nouvelle GT, pas
retuner A28 comme si elle était encore indépendante.

## A29 : une passe Luna + raccord CPU, gain réel mais gate OLR faux

Le mergeur de continuations est développé uniquement sur A27 consommée, puis
ses deux seuils et tout le protocole sont scellés avant ouverture de la page
BnF 00123453. Luna inspecte réellement huit JPEG avec 274 IDs opaques : 274
rôles exacts au contrat, 17 flux et aucune incertitude. Le raccord déterministe
produit 15 flux en 0,053 s évaluateur compris, sans nouvel appel VLM.

Résultat indépendant : F1 de paires 0,7132 brut, 0,7443 après raccord, contre
0,2277 pour la géométrie optimiste ; précision 1,0 dans les deux cas. L'ordre
sur les paires couvertes est 0,9984 mais son rappel de bout en bout seulement
0,5918. Le gate 0,90 échoue. L'audit post-score conserve six omissions de
convention et quatre fragments purs excédentaires ; aucun paramètre, candidat
ou original n'est modifié. `OrderedGroup` reste un flux PAGE conditionnel, pas
une vérité d'article.

## A30 : OCR VLM aveugle sur transcription manuelle BnF

Une nouvelle page française (`00123532`), issue d'un autre groupe de numéros
que les pages OLR A27/A29, a été gelée avant ouverture. Seize `TextRegion` ont
été tirées déterministiquement ; les polygones PAGE ont servi à fabriquer des
crops masqués avec 12 px de contexte et un minimum de 1 200 px de largeur. Le
lecteur ne voyait que les PNG, des IDs opaques et une consigne diplomatique ; ni
XML, ni texte de référence, ni sortie d'un autre modèle.

La passe primaire Luna obtient 52 éditions sur 3 004 caractères, soit 1,7310 %
de CER NFC strict et 2/16 régions exactes. L'escalade Sol, lancée seulement
après cet échec et donc conservée comme diagnostic post-hoc, obtient 44 éditions
(1,4647 %) et 2/16 exactes. Elle reste loin de 0 %. Aucun composite sélectionné
avec la GT n'est produit.

Vingt-quatre éditions Luna et vingt-cinq éditions Sol sont des substitutions du
tiret insécable U+2011 de la référence par `-`. Une vue de recherche corrigée,
calculée après score et sans changer la métrique scellée, abaisse Luna à 0,8440
% et Sol à 0,5739 %, avec 6/16 régions exactes. Des erreurs lexicales subsistent
(`5e`/`3°`, `Mme Faure`/`Mlle Fabre`, noms propres) et la référence contient au
moins un caractère de remplacement dans `judicia�es`, plus plusieurs lectures
qui demandent adjudication. La transcription manuelle BnF est donc beaucoup
plus utile que NewsEye pour ce test, mais elle n'est pas déclarée parfaite.

Conclusion : ni le crop haute résolution ni Sol ne reproduisent le 0 % rapporté
pour Claude/Gemini sous ce protocole strict. L'écart restant doit être séparé en
trois couches explicites : fac-similé diplomatique, normalisation retrieval et
adjudication humaine des lectures discutées. A30 est consommée.

## A31 : pixels originaux non masqués et contexte visible

À la demande de l'utilisateur, un Sol neuf relit les mêmes 16 cibles sans masque
ni contour rouge, avec 16 vues de contexte supplémentaires. Il n'accède ni aux
références ni aux anciennes réponses. CER normalisé 0,5739 %→0,5402 %, soit
17→16 éditions sur 2 962 caractères et 6→7 régions exactes. `5e`→`3e` et
`Mme Faure`→`Mlle Fabre` sont corrigés, mais deux autres noms régressent.
Une seule passe par condition ne sépare pas variabilité et effet de préparation.
La marge A30 était blanchie : elle ne constituait pas un vrai contexte.
Voir `unmasked-a31/RESULTS.md`. Aucun original ni gate indépendant n'est modifié.
# Dernière itération — A32 (2026-09-27)

Développement mesuré sur A28 consommé : filtrage CPU de composantes, satellites
et contrôle visuel sans contours. IoU moyenne 0,83882→0,89379; rappel IoU80
68,45→81,75 %, 385 mots améliorés / 15 régressés; 0,726 s de CPU supplémentaire.
Trois pertes de ponctuation confirmées : candidat non promu. Résultats, sources
primaires, paramètres, ablations et images dans `component-boxes-a32/`.
84 phases terminées; objectifs finaux toujours non atteints. Le CER normalisé
est la cible opérationnelle demandée; les anciens CER stricts restent des
diagnostics historiques. Aucun nouveau score OCR n'est produit par A32.
# Dernière itération — A33 (2026-09-27)

Le rattachement de ponctuation guidé par le texte est rejeté sur A28 consommé :
4 des 11 boîtes modifiées s'améliorent, 7 régressent; IoU moyenne
0,893795→0,893394 et rappel IoU80 81,746→81,689 %. L'inspection exhaustive
montre que le texte annonce le signe mais ne dit pas si A32 l'a déjà couvert;
certains blobs récupérés viennent de la ligne inférieure. Garder A32, pas A33.
La variante conservatrice suggérée par les aires est une observation post-score
à geler sur de nouvelles données. 85 phases; sept gates toujours faux.

# Dernière itération — A34 (2026-09-27)

La règle conservatrice A34 a été gelée puis mesurée sur 12 pages inédites de
trois ouvrages SBB : 515 lignes et 4 759 mots. A32 se transfère fortement face
à PERO natif (IoU moyen 0,8123 contre 0,6549; rappel IoU80 58,94 % contre
19,04 %), mais ne constitue pas des boîtes parfaites et reste conditionnel aux
lignes/texte/ordre oracle. A34 n'améliore qu'un mot et en dégrade six : rejet.

DAHN, TAPUS et Reichsanzeiger-GT ont aussi été contrôlés sur leur schéma réel :
leurs exemples inspectés sont au niveau ligne, sans géométrie `Word`; ils ne
peuvent donc pas servir de GT IoU mot. Le corpus A34 est allemand/latin et
livresque, pas français ni presse. Une réparation mécanique de l'adaptateur,
effectuée après ouverture mais avant tout score, empêche en outre de qualifier
l'évaluateur entier de gel parfait. 88 phases; sept gates toujours faux. Voir
`word-transfer-a34/RESULTS.md`.


## A35: recognized-word refinement

2026-09-27: `scripts/evaluate_native_refinement_a35.py` applies unchanged A32 to cached native recognized words. On consumed French A28, recall IoU≥0.8 improves 11.07% → 80.66%; on consumed German/Latin A34, 19.04% → 55.96%. Reference transcription/token count are removed from the refiner; reference line rectangles and synthetic baselines remain. No new OCR/VLM inference or CER improvement. Joint exact-text+IoU≥0.8 recall is 73.25% / 42.09%, and visual audit confirms neighboring-ink/punctuation failures. All project gates stay false. See `experiments/loop/native-refinement-a35/RESULTS.md`, `SOURCES.md`, `PROTOCOL.md` and raw measurements. Next: predicted lines plus an unopened reference set, without retuning these consumed pages.

## A36: full-page predicted lines

On one unopened four-page SBB work, PERO found 138/138 line counts with
97.06–100% per-page line recall at IoU 0.5. Unconditional A32 reduced word mean
IoU .648489 → .639549 by absorbing adjacent Fraktur-line ink. A consumed-data,
zero-parameter router that rejects vertical expansion reaches .698075 and
preserves A28/A34 gains. It must be frozen unchanged on A37. See
`predicted-lines-a36/RESULTS.md`; all seven project gates remain false.

## A37: frozen non-expanding router

The unchanged A36 rule passes its sealed local gate on four previously unopened
pages: native mean word IoU .568214 becomes .853595 and IoU80 recall .005085
becomes .686441, with strict improvement on every page. PERO predicts 101/101
line counts and 591 words for 590 references. Cost is 10.573 s full-page CPU
plus .284 s refinement/routing and zero VLM passes. Visual audit retains 11
local regressions, chiefly punctuation/token-boundary cases and one horizontal
ownership failure. This is local German/Latin validation, not perfect boxes or
French/OLR/OCR completion; all seven project gates remain false.

## A38–A40: three conservative guards rejected

Cached consumed-data ablations show that a single `alle` regression must not be
overfit. Width non-expansion collapses IoU80 on all datasets; full vertical
containment also loses; an equal-height translation guard is nearly neutral on
A37 but still regresses the French and earlier SBB sets. No inference or VLM was
rerun. Retain A37 and seek local line-ambiguity evidence instead.

## A41–A43: local line-ownership guards rejected

Three cached consumed-data experiments used PERO's predicted baselines,
`heights_v2`, and then source-image foreground. A41 rejects boxes that increase
overshoot beyond the local predicted line band; A42 compares all foreground
pixels with neighbouring predicted line centres; A43 applies the same idea only
to newly added foreground and requires a strict foreign-line majority. All
three reduce fixed-assignment regressions, but all lower mean IoU on A36 and
A37. The least harmful A43 changes 22/922 and 10/591 words, yet mean IoU falls
.698075→.696725 and .853595→.853119. No new OCR or VLM pass was used. All
candidates are rejected; A37 remains the frozen implementation candidate.

## A46–A47: independent transfer, then targeted VLM audit

PERO 0.7.0 plus unchanged A37 was run once on the 24 frozen BnL blocks. The
first geometry score exposed an evaluator unit bug and is preserved as invalid;
the amended evaluator converts declared `mm10` coordinates to documented
300-PPI pixels by `300/254`. On 12 French blocks, line IoU50 recall is .9952.
A37 improves word mean IoU .5512→.6159 and IoU50 recall .6696→.7358, while the
word reference remains diagnostic. French lexical CER is .2244%, with 9/12
exact blocks.

A47 sends only the seven known residual images to blind Luna, then blind Sol.
They agree exactly after retrieval accent folding, while both differ from the
immutable reference on probable annotation errors. Real PERO errors are also
confirmed. This post-score audit cannot be reported as independent zero CER;
human adjudication and a new page-level French/OLR holdout remain necessary.

## A48–A49: full pages, columns and articles

Three Finlam pages first revealed that legacy BBVLM merged six or seven columns
into one. Recurrent left-edge modes were developed on A48 and validated without
retuning on six new A49 pages: global order .6721→.8834, within-article order
.8717→.9880, and article-pair F1 .2032→.6632. The gains are independent but the
global gates remain false.

A single compact Luna pass on 33 masthead/title anchors found seven columns,
all 20 anchored articles and four sourced metadata values. It was worse than
geometry for article order (.7632) and headline `retrieval_fold_v1` CER against
non-adjudicated provider OCR remained .3279%. The next architecture pays the
VLM for semantics, continuations, title/metadata OCR and retrieval normalization,
not for cheaper physical columns or coordinates.

## A50–A51: selective semantic boundaries

A50 routed 50 ambiguous transitions on one consumed stress page to one blind
Luna pass. Adding its boundary decisions to title cuts improved article-pair F1
from .5869 to .9093, but the preparation used reference presence to omit
unannotated edges and is development-only.

A51 removed that leakage, froze eight new rows before opening content, and
opened only rows 216 and 164 for a pilot. Row 216 improved article-pair F1
.7148→.8397, but row 164 collapsed .2604→.1249 because Luna separated many
visually distinct notices that Finlam places inside two enormous provider
articles (173 and 67 zones). Macro F1 is .4876→.4823; global order is .8167
and within-article order .9762. All frozen gates fail. The six reserve rows stay
closed until provider containers and independently retrievable semantic items
have separate ontologies and scorers. See `finlam-boundaries-a51/RESULTS.md`.

Every future literature pass now receives an article-by-article record in
`PAPER_SUMMARIES.md`. The competing Claude branch is inspected before choosing
each new hypothesis; the first audit is `CLAUDE_BRANCH_AUDIT.md`.

## A57 — resumption integrity

Checkpoint bundling previously regenerated a legacy-only state, dropping A54-A56 registrations while retaining raw reports. The builder now preserves extension records and verifies artifact presence. Reports restored; regression test passes; all seven global gates remain false.

## A58 terminé
Voir chronicling-a58/RESULTS.md : 801 XML audités, réserve100 pages ; aucun Word, ordre automatique, défaut de nom train. Aucun critère global validé.


## A59 terminé
Sol natif aveugle rejeté : lexical24→57 éditions, deux témoins préservés ; référence0345 comporte quatre désaccords soutenus par l’image. Prochain test : bandes natives0455.


## A60 terminé
Bandes natives : Sol45→36 éditions lexicales, reste supérieur aux8 de Luna guard. Pas de promotion.


## A61 terminé
Candidat+bandes Sol :8→6 éditions lexicales, dont une modification régressive. Pas de promotion automatique. Rapports A57–A61 et commits distincts ; tous critères globaux restent faux.


## A62 — boucle active
File de tâches concurrentes et reprenables : voir CONTINUOUS_LOOP.md et queue-a62/RESULTS.md. Ne pas attendre la prochaine reprise si du travail utile est prêt. Neuf tests réussis ; aucun nouveau score OCR.

## A63 terminé dans la même session
File exercée sur une vraie lecture Sol et son score :6→4 éditions lexicales sur6lignes sélectionnées oracle, aucun score indépendant ni perfection. Voir next-a63/RESULTS.md. Prochaine action a64_prepare.
