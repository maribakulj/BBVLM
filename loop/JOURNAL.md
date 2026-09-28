# Journal de la boucle

## O01 — 2026-09-28 — une page, une passe Opus, zéro faute de lecture

Revue L01 faite avant (Greif 2025, Clérice 2026, OCR-EDR 2026). Protocole figé
(`o01/PROTOCOLE.md`), trois lecteurs à l'aveugle sur SBB borrdisc p. 18.
Opus page entière : 1 écart diplo sur 1049, et c'est la référence qui se
trompe (`oppeſer` pour `oppoſer`, vérifié à 4×). Bandes pleine résolution :
pas mieux (espaces autour des traits d'union). Sonnet : ſ lu f partout.
Détails : `o01/RESULTATS.md`. Premier jalon « OCR parfait sur une page »
atteint sur une page facile ; à généraliser (O02).

## O02 — 2026-09-28 — quatre pages : romain parfait, Fraktur entre 0,2 et 3 %

Adjudication aveugle de 86 lignes : la référence SBB a 1 à 9 caractères faux
par page. Romain : 0,000 % sur les deux lectures. Fraktur dense avec bandes :
0,215 % (une espace). Le consensus de trois lectures est **pire** que la
meilleure seule. Fautes résiduelles : diacritiques suscrits (résolution),
I/J, placement folio/signature, rares lexicales sur zones abîmées. Règles OCR-D
lues (L02) : la ponctuation se colle au mot précédent. → O03 : consigne OCR-D
explicite, page + bandes, pages jamais lues.

## O03 — 2026-09-28 — deux Fraktur jamais vues à 0,000 %

Consigne OCR-D niveau 2 explicite, page + bandes. betrdrzwt et curineux : une
lecture à 0 faute chacune après adjudication. Variance dominée par les signes
suscrits. Arbitre unique non fiable sur ů : double adjudication désormais.
Incident : ejngerez L2 écrasé par L1.

## G01 — 2026-09-28 — premières boîtes sur texte VLM

connexe tient CRITERE sur 4 pages sur 9 avec le texte lu par Opus ; le filtre
A32 d'astra perd en Fraktur (voisinage vertical), comme astra l'a vu en A36.

## Veille astra — 10:15

A36-A51 : routeur A37 (IoU80 68,6 % sur lignes prédites PERO), colonnes de
presse par modes du bord gauche (A48-A49), frontières d'articles par VLM
rejetées. Voir CONCURRENT.md.

## O04 — 2026-09-28 — zoom ×1,6 utile, double adjudication, règle d'inflexion

Zoom meilleur sur 3 pages sur 4. La double adjudication écarte les corrections
d'un arbitre isolé (9 « ů » sur helfkurt tombent). Découverte : 0 tréma dans
les 13 références SBB ; règle R1 (tréma → e suscrit hors pages à ů) :
351 → 215 fautes sur O02-O04 — développement, à valider en O05. Référence
buchdiss : grec et hébreu faux (32 car.).

## G02 — routeur A37 appliqué à connexe+A32

Horizontale A32, verticale jamais au-delà de connexe : IoU médian proche ou
meilleur que connexe partout (helfkurt 0,950 → 0,959, ejngerez 0,874 → 0,891),
frontières inchangées. Le pire cas d'actevedef (6,4 car.) est une boîte de
référence douteuse (« a. » large de 134 px).

## O05 — 2026-09-28 — validation : R1 réfutée en romain, a priori lexical

glauanno 0 %, fiscfrie 0 % sans R1 (2,74 % avec), heshwarh 0,07 %, catapabin
0,67 % dont « Marana » pour l'imprimé « Maruna » : le lecteur corrige vers le
nom connu. R1 réécrite (P2) : conditionnée à la déclaration « fraktur » du lecteur.

## S01 — kraken 7.1.1 installé (pip), segmentation blla en cours sur 17 pages.

## O06 — 2026-09-28 — P2 validée, variance entre passes = prochain verrou

BiedBern 0 % (deux passes) ; R1 conditionnée : 0 régression, gains en Fraktur.
Écart entre deux passes jusqu'à ×4 (baroegvi 0,60 / 2,57 %).

## S01/E01/G03 — premier ALTO bout-en-bout au critère gelé

kraken blla + resserrement sur l'encre du polygone + texte VLM + connexe :
CRITERE tenu sur 4 pages sans aucune référence en entrée. Fraktur serrés :
frontières < 95 %.

## O07 — 2026-09-28 — P3 validée : 3 pages sur 4 à 0 faute

Deux passes + arbitrage des 12 lignes en désaccord sur 133 : 730277879 (A à
2,06 %) → 0 %, albedm 0 %, berirev 0 %, Aphoq 0,80 % (grec, erreur commune).
Premier ALTO produit par la chaîne entière, valide XSD 4.4 ; au mot : texte
exact ET IoU≥0,8 de 61 à 92 %.

## Audit — réclame de drabnota (signalée par astra, A52)

Référence et notre arbitre O02 : « wort ». Lecture aveugle Opus sans candidats
(recadrage 4×) : « werct » ; astra : « werck » ; lecture directe de
l'orchestrateur : « wert ». Trois lectures indépendantes contre une : la
2e lettre est un **e** ; notre référence adjugée se trompait. Fin du mot
indécidable (t / ct / ck). Conséquence de méthode : un verdict X/Y d'un
seul arbitre n'est pas sûr non plus. Désormais, toute page annoncée à 0 %
subit un audit : relecture aveugle **sans candidats** de ses lignes arbitrées
par un second Opus ; un désaccord rend la ligne « contestée ».

## Audit O07 — 4 lignes contestées sur les deux pages à 0 %

Relecture aveugle sans candidats : 13 lignes concordantes, 4 contestées
(å/aͤ, ſ/f, ſs/ß, ꝛ/r, t/c). Les 0 % se disent désormais avec leur nombre de
lignes contestées.

## O08 (en cours) — OLR des livres dans la même passe

Rôle de chaque ligne 81-100 % exact, ordre des régions 0,90-1,00, régions
parfaites sur herrleyc/euanaua ; granularité à préciser (culmsent : un
proverbe = un paragraphe pour le lecteur, un bloc pour la référence). ALTO avec
TextBlocks typés + ReadingOrder, valide XSD.

## R01 — recherche plein texte : 100 % sur albedm, 53-93 % ailleurs

Métadonnées bibliographiques : aucune référence accessible (MODS vides,
catalogues SBB/VD17/K10plus bloqués par le proxy).

## O08 — bilan texte : erreurs communes aux deux passes

culmsent 0,075 %, euanaua 0,20 %, DasWeL 1,40 %, herrleyc 1,82 %. Restes =
ů pour uͤ sur des mots à inflexion, ſ pour ß : erreurs partagées que
l'arbitrage des désaccords ne voit pas. Littérature L06 : o suscrit (ů) = uo,
e suscrit = inflexion → R2 par l'étymologie. Consigne P5 à tester en O09.

## R2 déterministe (lexique) — développement

`outils/r2.py` : ů → uͤ si la forme en ü l'emporte d'au moins 1 zipf dans le
lexique allemand moderne (wordfreq). Sur toutes les lectures O02-O08 : 544 →
518 fautes, herrleyc 18 → 6 et 20 → 8, 0 régression. Intégrée à p2.py.
Limite constatée en O09 : **bas-allemand** (geomeikud : Krůdern, frůndt) —
le lexique haut-allemand ne tranche pas ; la référence y note uͤ.

## O09 (en cours) — P5 : OLR F1 ≥ 0,91 sur 3 pages sur 4

Granularité des régions corrigée par la consigne : AmmoLIBR 0,91, BrenBreu
1,00, baltdiss 1,00 ; geomeikud 0,29 (titres d'items « i. Jsop » lus comme
titres, la référence les met dans le paragraphe). Texte : notation MUFI en zone
privée de l'abréviation « -que » (U+F50D, U+E8BF) contre « q́; » lu — convention
non documentée même chez dinglehopper.

## O09 — 2026-09-28 — chaîne complète : 2 pages à 0 faute, 2 à 1 caractère

Texte P3 0 / 0 / 0,06 / 0,16 % ; OLR régions 0,91-1,00 sur 3 pages ; ALTO
texte+IoU80 79-92 % ; recherche 88-97 %. Routeur A37 (astra) adopté pour les
boîtes après mesure ; alignement des manchettes par rôle adopté après mesure.

## S02 — manchettes fusionnées par kraken : coupe au bord de colonne

Diagnostic des lignes en échec (CRITERE sur la chaîne finale, 12 pages : 3
pages ✓, les autres surtout par 1-5 lignes en échec) : kraken fusionne la
manchette avec la ligne du texte courant (même ligne de base), collée à
10-15 px (moins qu'une espace). `outils/coupe.py` : bord du texte justifié =
mode des extrémités de lignes ; ligne qui le dépasse coupée dans un vrai blanc
(≥ 3 px) près du bord. Lignes trouvées : berirev 40 → 47/48, herrleyc 31 →
36/36, Aphoq 28 → 31/32, BrenBreu 35 → 36/36. Fausses coupes sur les pages à
vers/listes → coupe appliquée **seulement si le lecteur signale des manchettes**
(rôle P5). herrleyc : 36/36 lignes placées, rappel IoU80 0,66 → 0,78,
**recherche 53 % → 91 %**.

## O10 — 2026-09-28 — validation de la chaîne gelée sur 4 œuvres neuves

Texte P3 : backhart **0** (0/896), hackherz 1 car., heptaldai 9, herrkurt 40
(33 de notation : florin/groschen en PUA, ½). ALTO 4/4 valides ; CRITERE ✓
sur backhart seulement. Diagnostic boîtes : heptaldai = lignes inclinées
(boîtes de mots), herrkurt = segmentation, hackherz = page en regard (écartée
par l'alignement) + réclame non détectée. Détail : o10/RESULTATS.md.

## A2 — 2026-09-28 — renverser la référence exige deux arbitres

Constat O10 : un arbitre seul a renversé ﬂ → ſl sur deux « fl. » (florin),
contredit par un second arbitre aveugle. Règle A2 (bilan_adj.py ; BBVLM_A1=1
rend l'ancienne) : tout texte retenu autre que la référence distribuée, texte
neuf OU choix de la lecture, n'est retenu que si un second arbitre
indépendant écrit le même. Second arbitrage aveugle des 167 renversements à
arbitre unique d'O02-O10 (4 arbitres Opus, verdicts dans adjudication_a2/).
Effet : **aucune page à 0 % ne bouge** ; quelques renversements tombent
(ejngerez 22 → 20 car. de référence corrigés, colechri 6 → 3, herrleyc 6 → 3,
heptaldai 6 → 4, herrkurt 5 → 3) ; CER final herrleyc 18 → 21, heptaldai 7 → 9.
Les résultats antérieurs tiennent sous la règle plus stricte.

## P6 — 2026-09-28 — notation des signes spéciaux (développement sur herrkurt)

Deux passes P6 sur herrkurt : les jetons ASCII `{florin}` / `{groschen}`
(convertis en U+F2E8 / U+F2E9 par p2.py) et « ½ » ramènent 42/39 → **5/9**
éditions. La première version (demander le PUA brut) échoue : 0 PUA émis.
Leçon : un VLM n'écrit pas la zone privée ; il faut un jeton lisible et une
table de conversion déterministe. Validation requise sur pages neuves (O11).

## B01 — centre local de ligne (L07) — en cours

Boîtes calculées sur la ligne redressée autour du centre local
(CenterNormalizer d'OCRopus). heptaldai, lignes de référence : ≤0,5c
78,95 → 84,8 %, IoU méd 0,639 → 0,698, mais pire 1,69 → 4,03 ; lignes kraken :
78,4 → 79,5 %, IoU 0,605 → 0,616. Banc complet en cours.

## O11 — 2026-09-28 — consigne P6 sur 4 œuvres neuves

Texte P3 contre référence adjugée (deux arbitres dès le départ, règle A2) :
852691769 **0** (80/80 lignes, page-tableau latine), chridiss 4, branchri 6,
extraudeu 43 (41 = une ligne visuelle qui porte deux lignes de référence :
fin de paragraphe + « Signatum… » à droite ; L08, règle candidate P7). P6 ne
dégrade rien ; adoptée dans la chaîne. Arbitre P3 : recadrages faux sur la
page-tableau → consigne de repli sur les bandes (consigne_arbitre_P3.md),
0 faute après. Détail : o11/RESULTATS.md.

## S03 — ordre de lecture par XY-cut (L09) — adopté

Union-find sur le recouvrement horizontal : un titre pleine largeur fond les
colonnes (852691769). XY-cut récursif (colonnes puis bandes, blancs ≥ 0,5 h).
20 pages O07-O11 : identique partout sauf 852691769, texte+IoU80 0,062 → 0,136.

## S04 — alignement lecture→lignes : chasse ∝ corps pour les gros corps — adopté

extraudeu : le titre « EXTRACT » (7 car., 844 px) décalait tout
l'alignement (texte+IoU80 0,131). Largeur/hauteur pour toutes les lignes :
extraudeu 0,641 mais herrleyc 0,393 → 0,183 (hauteurs kraken bruitées).
Correction seulement des lignes > 1,4 × hauteur médiane : extraudeu 0,641,
aucune régression sur les 5 autres pages testées (herrleyc, berirev,
baltdiss, heptaldai, 852691769). Seuil choisi une fois, à valider sur O12.

## B01 — centre local : mitigé, gardé sous seuil (non adopté)

Banc complet (16 pages, lignes réf. et kraken) : gain sur lignes inclinées
(herrkurt ≤0,5c 84,7 → 90,7 %, IoU 0,816 → 0,887 ; 730277879 89,3 → 95,9 % ;
berirev pire 7,17 → 4,33), perte sur pages droites (AmmoLIBR 96,9 → 92,2 %,
DasWeL 97,6 → 94,0 %, IoU −0,01 à −0,03). Redressement désormais réservé aux
lignes dont la dérive dépasse 0,25 h ; à re-mesurer avant adoption.

## O12 — 2026-09-28 — chaîne P6 sur 4 œuvres neuves (texte)

P3 final contre référence adjugée (A2) : erobdefoa **0**, durrgeda 1,
emmeprac 9, herbdulc 10. herbdulc : 10 = cinq ů (anneau imprimé, deux
arbitres concordants) lus uͤ à cause de la règle étymologique P5 → règle L06
réfutée pour cet imprimeur. R2 mesuré partout (O07-O12) : utile seulement sur
herrleyc (41 → 17), neutre ailleurs. Consigne P7 (forme d'abord +
`#INFLEXION` déclaré, R1/R2 conditionnés ; + règle L08). Placement : banc
S05 en cours, décision avant lecture des scores ALTO d'O12.
