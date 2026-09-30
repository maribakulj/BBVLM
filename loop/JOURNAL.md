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

## P7 — 2026-09-28 — rejetée (développement sur herbdulc et herrleyc)

P7 = P6 + « forme d'abord » + déclaration `#INFLEXION` par le lecteur (R1/R2
conditionnés) + règle L08. Deux lectures par page :
- herrleyc (inflexion en e suscrit selon la référence adjugée) : les deux
  lecteurs déclarent « anneau » → A+B 17 → 41 éditions (fůr, Sůnde, důnner).
- herbdulc (anneau selon deux arbitres) : A déclare e, B anneau ; B coupe
  R1 et écrit ä/ö en points → A 10 → 20, B 11 → 36 ; blancs perdus dans les
  renvois marginaux.
Conclusion : à la résolution des bandes/zooms, le lecteur ne distingue pas un
anneau d'un e réduit ; les arbitres, sur la ligne recadrée en pleine
résolution, le font. P6 reste la consigne. Piste suivante : décider le signe
d'inflexion par page sur quelques mots recadrés en pleine résolution (passe
ciblée courte), puis l'appliquer à la page.

## I01 — 2026-09-28 — signe d'inflexion décidé par page en pleine résolution — adopté (à valider O13)

Après l'échec de P7 : jusqu'à 4 lignes à mots « u + signe » recadrées en
pleine résolution ; un arbitre classe la FORME de chaque signe (anneau / e) ;
seuls les mots à inflexion (forme moderne en ü, lexique R2) votent et sont
convertis (DasWeL : ů = uo et uͤ = ü sur la même page) ; garde : ≥ 3 votes et
≥ 3/4 d'accord (extraudeu : 2 votes « anneau » contredits par deux arbitres
concordants sur l'image). 16 pages O07-O12 à signes : **147 → 129**
éditions, herrleyc 21 → 9, herbdulc 10 → 4, **aucune régression**. Préparé
avec l'arbitrage P3 (sur la lecture A) : même appel d'arbitre, pas de passe
VLM supplémentaire. Développé sur ces pages → validation O13.

## S05 — 2026-09-28 — ancrage Tesseract des lignes (L10) — adopté

Banc complet 20 pages (O07-O11), chemin réel de la chaîne (avec rôles),
texte+IoU80 : ancien (union-find + largeur) / S03+S04 / **S05**. S05 égale ou
dépasse sur 18 pages ; 852691769 0,074 → **0,669** (80/80 lignes placées au
lieu de 47), extraudeu 0,131 → 0,648, berirev 0,791 → 0,816, culmsent
0,778 → 0,794, AmmoLIBR 0,824 → 0,835 ; reculs AphoqvSuS 0,805 → 0,788,
geomeikud 0,787 → 0,778. Adopté par défaut AVANT lecture des scores ALTO
d'O12 (validation). Tesseract : un modèle par écriture (script/Fraktur ou
lat), 13 s pour 86 lignes. Note : le banc S03/S04 initial mesurait le chemin
sans rôles (bug du banc, corrigé) ; S03/S04 ne changent rien sur le chemin
réel hors 852691769/extraudeu.

## O12 — 2026-09-28 — ALTO : S05 et I01 validés sur pages neuves

I01 : herbdulc 10 → 4, rien d'autre ne bouge. S05 : texte+IoU80 meilleur sur
3 pages sur 4 (durrgeda +0,047, herbdulc +0,028 et 40/41 lignes placées au
lieu de 34, erobdefoa 0,983), recul sur emmeprac (0,779 → 0,752).
**erobdefoa : première page parfaite de bout en bout** — 0 faute de texte,
CRITERE ✓ (≤0,5c 100 %, pire 0,0). Sur les autres pages, CRITERE bloqué par
3-4 lignes en échec (nombre de mots), pas par les frontières.

## S06 — 2026-09-28 — lignes manquées par projection (L11) — non intégré

Titres d'apparat de durrgeda (430 px, initiales florales) : kraken ne les
trouve à aucune échelle (1 → 1/8, mesuré) ; la ligne d'adresse « JENA… » est
retrouvée à 1/2. Bandes d'encre hors lignes kraken (profil horizontal, seuil
calé sur l'encre des lignes kraken, zone de texte, composantes de bord
exclues) : titres de durrgeda retrouvés en partie seulement, bandes parasites
sur la page-tableau (accolades, filets). Gain rare, risque de bruit : non
intégré (`outils/bandes.py` gardé comme outil de diagnostic).
Diagnostic CRITERE O12 : échecs = blancs du texte lu (emmeprac, 4 lignes :
fautes de texte déjà comptées) + lignes non trouvées par kraken (titres
d'apparat durrgeda, courtes références marginales herbdulc).

## O13 — 2026-09-28 — chaîne complète gelée sur 4 œuvres neuves

Texte final contre référence adjugée : caladr **0**, AyrmThes 1, bankgraf 2,
brochrnx 2 ; CRITERE ✓ sur caladr et bankgraf. **caladr : deuxième page
parfaite de bout en bout.** I01 neutre (aucune décision), S05 égal ou mieux.
Restes : uniquement des blancs autour de la ponctuation (« v.c. », « .— »,
« ⸗ » isolé) — prochaine cible du texte.

## OLR O11-O13 (12 pages neuves) — 2026-09-28

Rôle exact ≥ 0,95 sur 8 pages ; F1 même région ≥ 0,91 sur 9. Écarts =
conventions de la VT : page de titre (durrgeda) = une seule région heading
+ 29 régions drop-capital (lettrines florales), le lecteur la découpe en
paragraphes (rôle 0,36) ; régions sans type (brochrnx, 9 lignes « other ») ;
page-tableau (852691769 : 48 régions de référence contre 16 lues). Aucune
règle ajoutée pour un exemple unique.
Métadonnées d'œuvre : pas de vérité accessible (MODS vide dans le dépôt SBB ;
catalogues K10plus, stabikat, VD17 refusés par la politique réseau).

## P6b — candidate (blancs après ponctuation), test A/B prévu en O14

Restes O13 = blancs autour de la ponctuation (« v.c. » lu « v. c. »,
« reden.—Aber »). OCR-D niveau 2 : espaces seulement entre mots, ponctuation
collée au mot précédent — rien n'impose un blanc après une ponctuation serrée.
P6b = P6 où, après la ponctuation, on suit l'imprimé.

## O14 — 2026-09-28 — A/B P6 contre P6b : P6b rejetée ; biais d'arbitrage corrigé

P6b (après ponctuation, suivre l'imprimé) : 87 éditions contre 73 pour P6
(référence distribuée) ; contre la référence adjugée 57 contre 63 mais
baurodwe +3 → rejetée selon le critère figé. La VT SBB met une espace après
une virgule même serrée : la règle P6 est la bonne pour les virgules.
Leçon : la consigne d'adjudication d'O14 énonçait la règle testée → référence
adjugée biaisée. Consigne d'adjudication désormais figée dans un fichier
(`consigne_adjudication.md`, convention de la VT). La variance entre lectures
domine les petits effets sur 4 pages.

## Audit A3 — 2026-09-28 — le même biais dans les adjudications antérieures ?

Les consignes d'arbitrage d'O02-O13 disaient « espaces tels qu'imprimés ».
Renversements retenus (deux arbitres concordants) qui suppriment un blanc
après ponctuation : **15**, sur 5 pages (drabnota « /», abdipre « Ioã. 14. »
→ « Ioã.14. », hackherz « 2. Cor. XII », extraudeu « L. S. », bankgraf
« .— »). Vue prudente (ces seuls cas rendus à la référence distribuée) :
abdipre 3 → 7, extraudeu 43 → 44, hackherz et bankgraf inchangés, drabnota
26 → 21. **Aucune page annoncée à 0 % ne change de statut.** Les deux vues
sont désormais rapportées quand elles diffèrent ; les adjudications futures
suivent `consigne_adjudication.md`.

## V01 — 2026-09-28 — combien de passes VLM ? (16 pages neuves O10-O13, sans nouvelle lecture)

Contre les références adjugées : une lecture seule A 132 éditions ; A + I01
**126** ; B + I01 131 ; chaîne complète (2 lectures + arbitre P3 + I01)
**122** ; pages à 0 : 3 / 3 / 4 / 4. La deuxième lecture complète et l'arbitre
évitent ~5 % des erreurs restantes pour deux fois plus de lecture VLM, et
l'arbitre en introduit parfois (bankgraf : B 0 → final 2 ; heptaldai A 7 →
final 9). I01 (passe courte ciblée) apporte l'essentiel du gain
(herbdulc −6). Mode économe ajouté à la chaîne (lecture A seule, I01 dans un
appel court) ; mode qualité inchangé. Piste : cibler la seconde passe sur les
lignes à risque plutôt que relire toute la page.

## T01 — 2026-09-28 — Tesseract comme signal de lignes à risque — négatif

Lecture A seule, 533 lignes des 16 pages O10-O13, 55 fausses (référence
adjugée). Distance lecture ↔ OCR Tesseract de la ligne kraken ancrée :
**AUC 0,57** ; revérifier les 20 % de lignes les plus contradictoires ne
capte que 16/55 lignes fausses (30 % : 26/55). Les erreurs restantes sont
fines (blancs, signes suscrits, ſ/s) et Tesseract (tessdata_best, Fraktur)
trop bruité pour les juger — conforme à astra A53 (CTC utile comme
contradiction grossière, pas comme juge). Le désaccord entre deux lectures VLM
reste le seul détecteur efficace de ces erreurs ; pas de passe ciblée par
Tesseract. Le mode économe garde donc son coût en qualité (~5 %).

## Recherche O10-O13 (16 pages neuves, ALTO de la chaîne actuelle) — 2026-09-28

Rappel des occurrences (terme + boîte IoU ≥ 0,5) : ≥ 0,95 sur 6 pages
(erobdefoa 1,00, backhart 0,99, branchri 0,98), 0,85-0,93 sur 7, 0,80
herrkurt, 0,77 852691769 (0,09 avant l'ancrage S05 : ALTO reconstruit), 0,63
heptaldai (lignes inclinées : boîtes). Toutes les lignes d'O10-O11 sont
désormais placées.

## B01 — re-mesure sous seuil (24 pages O07-O13) — non adopté

Seuil 0,25 h : identique à Route sur les pages droites, mais ne se déclenche
presque plus sur les pages inclinées (heptaldai IoU méd 0,605 → 0,611 ;
herrkurt ≤0,5c 84,65 → 83,72). Sans seuil, gain sur inclinées et perte sur
droites. La dérive estimée sur l'encre (CenterNormalizer) est trop bruitée.

## B02 — redressement par la ligne de base kraken — en banc

Même redressement, dérive lue sur la ligne de base (polyligne kraken, jusqu'ici
inutilisée). 4 pages, texte+IoU80 route → base (seuil 0,15 h) : heptaldai
0,343 → 0,418 (IoU méd 0,611 → 0,760), herrkurt 0,470 → 0,583, herbdulc =,
bankgraf 0,899 → 0,855. Banc 24 pages, seuils 0,15 et 0,30, en cours.

## B02 → B04 — 2026-09-28 — redresser seulement les pages penchées

Banc B02 (20 pages sur 24 avant arrêt), texte+IoU80 route / base 0,15 :
gains 730277879 0,725 → 0,824, extraudeu 0,648 → 0,821, herrkurt 0,470 →
0,583, heptaldai 0,343 → 0,418, culmsent, baltdiss, backhart ; pertes berirev
0,816 → 0,758, geomeikud 0,778 → 0,732, AphoqvSuS, AmmoLIBR, erobdefoa
0,983 → 0,975. Seuil 0,30 : quasi neutre. B03 (accord pente base/encre) :
supprime aussi les gains — l'estimation par l'encre est le maillon faible.
Diagnostic : les pages gagnantes ont une dérive médiane des lignes de base
≥ 0,17 h (59-81 % des lignes > 0,15 h), les perdantes ≤ 0,14 h (8-41 %) :
sur une page droite, les rares lignes « penchées » sont du bruit de ligne de
base. **B04** : redressement activé seulement si la dérive médiane de la page
≥ 0,15 h (propriété de page, comme le deskew). Seuil fixé sur ces pages de
développement ; validation sur les 4 pages O14 (boîtes jamais mesurées).
Banc propre route / B02 / B04 sur 28 pages en cours.

## B04 — 2026-09-28 — adopté (banc propre 32 pages O07-O14)

Somme texte+IoU80 : Route 24,78 ; B02 (redressement partout, seuil 0,15 h)
25,00 ; **B04 (pages penchées seulement) 25,24**. Pages de validation O13-O14
(8 pages, jamais utilisées pour le seuil) : B04 = Route partout (gain
d'AyrmThes 0,856 → 0,906 manqué) ; B02 y perd sur baurodwe −0,053, dalarie
−0,051, bankgraf −0,044, brochrnx −0,037. Gains B04 : extraudeu +0,173,
herrkurt +0,113, 730277879 +0,099, heptaldai +0,075, culmsent +0,015 ; seul
recul erobdefoa −0,008. Adopté par défaut dans vers_alto.py (repli Route si
pas de ligne de base, p. ex. lignes coupées par S02). CRITERE.md (e01) reste
mesuré avec Route (lignes sans ligne de base).

## B05 — hauteur pleine sur la bande redressée — négatif

heptaldai après B04 : IoU méd 0,76, boîtes coupées en bas (y1 −6 px méd,
−14 px p10). Garder la hauteur pleine de la ligne sur la bande redressée :
heptaldai 0,418 → 0,378, herrkurt 0,583 → 0,477, extraudeu 0,821 → 0,669,
730277879 0,824 → 0,796 (l'encre des voisines revient). Réduction actuelle
gardée (variante sous BBVLM_REDRESSE_PLEIN=1).

## O15 — 2026-09-28 — chaîne gelée sur 4 pages neuves plus difficiles (latin, XVIe)

Final contre référence adjugée : busmexpo 2, eberbrev 14 (1 en vue norm :
tirets ⸗/-), cingdei 13, buchdas 37 (signe sur u, arbitres opposés). Boîtes
IoU méd 0,93-0,96, CRITERE ✓ busmexpo, recherche 0,91-0,96. Défaut P3 : les
lignes portées par la seule lecture B étaient perdues (cingdei : 3 numéros
marginaux) → correctif P3b. Les arbitres divergent sur des conventions de
forme (tiret de fin de ligne, points contre e suscrit) : la référence tient.

## P3b — 2026-09-28 — lignes portées par une seule lecture : mécanisme en place

cingdei : les 3 lignes de B seule (« 64. », « 65. », « 66. ») deviennent des
tâches ; l'arbitre les écarte : **numéros manuscrits à l'encre** dans la
marge, non imprimés. La référence SBB les transcrit. Question de convention
(la VT transcrit les annotations manuscrites anciennes ; la consigne P6 n'en
dit rien) — notée, pas de règle pour un cas unique. Le mécanisme P3b est
adopté (sans effet sur les 3 autres pages d'O15).

## Tiret de fin de ligne : convention ou glyphe ? (toutes les références, 50 pages)

Fin de ligne dans les VT SBB : pages romaines « - » 133 / ⸗ 49, fraktur ⸗ 100
/ « - » 13. Mais les pages sont homogènes (busmexpo ⸗ 14/0, eberbrev 13/0,
BrenBreu 13/0 en romain ; heptaldai « - » 3/0 en fraktur) : c'est le glyphe de
l'imprimeur, pas l'écriture. eberbrev : tirets empâtés, lecteurs « - »
partout, référence ⸗, arbitres opposés. Rien à changer à la consigne (« trait
double oblique → ⸗ ; simple → - ») ; l'homogénéité par page est une contrainte
exploitable si un jour une passe de glyphe ciblée (comme I01) est justifiée.

## A3 (rapport) — 2026-09-28 — référence rejetée par les deux arbitres, correction contestée

Quand les deux arbitres rejettent la référence mais proposent deux
corrections différentes, A2 garde la référence (fautive) et compte nos
lectures fausses. Ces lignes sont désormais rapportées à part, comme
indécidées (bilan_adj.py). O15 : buchdas 37 → **0,55 %** hors 11 lignes
indécidées (VT « ii » pour ü) ; busmexpo **0 %** hors 1 ligne (ꝗ/ꝙ). Les
deux chiffres (avec et sans indécidées) sont toujours donnés.

## L1 — 2026-09-28 — abréviation latine « -que » : codage PUA de la VT — adopté

VT SBB : q + ꝫ final codé en ligature MUFI PUA U+E8BF (12 occurrences),
U+F50D avec accent (5). Lecteurs : « qꝫ » (Unicode) ou « q; ». Conversion
déterministe dans p2 (et à la fusion P3) : qꝫ → U+E8BF, q́ꝫ → U+F50D.
Mesure A+B, toutes pages : référence distribuée 1 115 → 1 059 éditions ;
référence adjugée 638 → 694 d'abord (!), car les arbitres avaient « corrigé »
U+E8BF en « qꝫ » — une équivalence d'encodage prise pour une correction de
lecture. Correctif du bilan : le texte des arbitres passe par la même table
PUA avant comparaison. Alors 702 → **646**, aucune régression (busmexpo 30 →
6, AmmoLIBR 22 → 11, culmsent 14 → 2). Les scores finals déjà publiés restent
identiques (AmmoLIBR 0, culmsent 1, busmexpo 2, cingdei 13) ; les sorties
suivent désormais le codage de la VT.

## L2 — 2026-09-28 — apostrophe : convention de la VT (' droite) — adopté

Inventaire des fautes résiduelles O10-O15 : « ’ (réf.) → ' (lu) » 10 éditions,
toutes sur dalarie (O14). Les références distribuées codent l'apostrophe en
' U+0027 (29 pages, aucune ’) ; les lignes directrices OCR-D ne prescrivent
rien (L12, règle jamais rédigée). Les ’ des références adjugées venaient des
arbitres, à qui la consigne demandait « l'apostrophe telle qu'imprimée » :
artefact de convention, comme L1. Correctifs : ’ → ' dans p2, à la fusion
P3 et dans le texte des arbitres au bilan (BBVLM_APOS=0 pour l'ancien
comportement) ; consigne_adjudication.md : « apostrophe toujours ' droite ».
Mesure (référence adjugée A2, sorties finales refondues, 22 pages O10-O15) :
226 → **215** éditions ; dalarie 10 → **0** (7ᵉ page neuve à 0) ;
852691769 reste à 0 (D’ARGENTVILLE lu ’, désormais ') ; aucune régression.
C'est une correction de convention d'évaluation, pas un gain de lecture.

## E-dalarie — 2026-09-28 — troisième page parfaite de bout en bout

dalarie (O14), après L2 : texte **0** faute contre la référence adjugée ;
boîtes (kraken G03 + Route, e01) : lignes 21/21 trouvées (IoU méd 0,952),
0 ligne en échec, frontières ≤ 0,5c 97,3 %, pire 1,39c, IoU méd mots 0,929 →
**CRITERE ✓**. ALTO : 136/136 mots placés, texte+IoU80 0,927.
Pages parfaites (texte 0 + CRITERE ✓) : erobdefoa, caladr, dalarie.

## R-inv — 2026-09-28 — inventaire des fautes restantes (pages à ≤ 9 éd., après L2)

Aucune classe déterministe dominante ne reste. Par type :
- blancs de ponctuation (8) : réf. serrée là où la VT met d'ordinaire une
  espace (goclprop « gentis,quæ », « &ſpecies », « exalio » ; AyrmThes
  « v.c. » ; bankgraf « .—Aber » ; hackherz « eſtquod ») — la VT n'est pas
  homogène d'une page à l'autre ; aucune règle ne couvre les deux cas ;
- ſ/f et n/u (8) : lecture (emmeprac, goclprop, heptaldai, chridiss) ;
- ⸗/- en fin de ligne (3, heptaldai) ; ů/uͤ mêlés dans la même page
  (herbdulc, 2 : la VT mêle les deux signes, I01 ne peut pas les suivre) ;
- signes rares : ꝛ abréviatif (durrgeda « Hꝛn. »), ✝ lu †, ñ/n̄.
Conclusion : le texte des pages courantes est au plancher des conventions
de la VT (≤ 2 éd.) ; les gains restants viennent des pages dures (herrkurt,
extraudeu, buchdas, cingdei) ou d'une relecture VLM ciblée ſ/f.

## C-balayage — 2026-09-28 — CRITERE (e01, Route, kraken G03) sur les 24 pages O10-O15

✓ sur **10/24** : backhart, branchri, erobdefoa, bankgraf, caladr, aepidisp,
baurodwe, dalarie, busmexpo (+ 0 faute de texte : erobdefoa, caladr, dalarie).
Échecs, par cause :
- lignes en échec seules, frontières bonnes (≤ 0,5c ≥ 98 %, pire < 2c) :
  chridiss, durrgeda, AyrmThes, goclprop, emmeprac, cingdei, eberbrev —
  nombre de mots différent de la VT (blancs de ponctuation déjà comptés au
  texte) ou lignes absentes de kraken (chridiss 33/37, durrgeda 14/17,
  eberbrev 28/29) ;
- frontières : heptaldai (78 %, IoU 0,61, page gondolée ; B04 non évalué
  ici), herrkurt (85 %), hackherz et buchdas (pire 9-11c, lignes de texte
  fautif), 852691769 (58/68 lignes).
Les deux leviers : lignes manquées par kraken (4 pages) et le gondolage
(heptaldai). Le reste suit le texte.

## S07 — 2026-09-28 — couper les lignes kraken aux gouttières (L13) — rejeté

Diagnostic des lignes réf. non trouvées (IoU < 0,5) sur O11-O15 : notes en
deux colonnes fusionnées par kraken (chridiss, 4 lignes), manchettes de
gauche collées au texte (herbdulc 3, buchdas 1), titres d'apparat à
initiales géantes (durrgeda 2), ligne double (extraudeu), signature (eberbrev).
S07 (`outils/gouttiere.py`) : blanc de colonne ≥ LARG·h, aligné avec un blanc
d'une ligne voisine, et ≥ RAPPORT × l'espace de mot médiane de la ligne.
Banc 36 pages O07-O15 (lignes trouvées IoU ≥ 0,5, total 990/1032) :
LARG 0,5 : chridiss 33 → 36 mais 979 au total (erobdefoa 32 → 28, dalarie
21 → 18, backhart 22 → 19) ; RAPPORT 2,0 : 990 (852691769 +2, dalarie −2,
chridiss 0) ; RAPPORT 3,0 : aucun effet. Cause : la gouttière des notes de
chridiss (38-53 px, espaces de mots 19-21) a la taille des blancs des titres
espacés de dalarie (50-53 px) ; la géométrie seule ne les sépare pas.
Non intégré. Piste : coupe guidée par le texte (une ligne kraken dont l'OCR
d'ancrage contient deux lignes lues, S08).

## S08 — 2026-09-28 — scinder une ligne kraken portant deux lignes lues (coupe guidée par le texte) — adopté

Suite de S07 : c'est le texte, pas la géométrie, qui dit qu'une ligne kraken
en porte deux. `outils/scinde.py` : si l'OCR d'ancrage (Tesseract, S05) d'une
ligne kraken est plus proche de la concaténation de deux lignes lues (A puis
B, |i−j| ≤ 6 : notes en colonnes lues colonne par colonne) que de toute ligne
seule (gain ≥ 0,15, distance ≤ 0,35), coupe au plus large blanc proche de la
proportion |A|/(|A|+|B|). Appliqué avant la coupe des manchettes S02.
Lignes trouvées (IoU ≥ 0,5, 36 pages O07-O15, 990/1032) : gain 0,25 → 994,
0,15 → 1000, 0,08 → 1003 ; aucune page ne perd de ligne à aucun seuil ; 0,15
retenu (0,08 baisse la précision berirev, herrleyc).
ALTO bout en bout (texte+IoU80, 36 pages) : 28,444 → **28,551** ; berirev
0,816 → 0,865, chridiss 0,666 → 0,724 ; les 34 autres identiques (aucune
régression). BBVLM_SCINDE=0 pour l'ancien comportement.

## N01 — 2026-09-29 — vue « glyphe » : ne plus compter fausse une passe juste pour son codage — adopté

Question du mainteneur : les passes sont-elles fausses, ou seulement codées
autrement que la VT ? Inventaire des écarts résiduels (vue diplo, 34 pages
adjugées) : une part n'est que du codage — U+E8BF contre « qꝫ », U+F50D contre
« q́ꝫ », ½ contre « 1/2 », ñ contre n̄ (trait nasal), ϑ/θ, ϖ/π, point médian
U+00B7/U+2027, apostrophes. L1 et L2 les traitaient au cas par cas.
Solution générale (`outils/glyphe.py`, vue `glyphe` de cer.py) : deux textes
sont égaux s'ils montrent les mêmes signes. (1) Unicode canonique ; (2) chaque
PUA de la table de codage OCR-D est remplacé par la séquence Unicode que DÉCRIT
son nom, dérivée automatiquement (« q ligated with final et » → q + ꝫ ; « n
with medium high macron above » → n + U+0304 ; « ligature long s descending
t » → ſt) : 67/97 dérivés, les 30 autres (signes d'abréviation, lettres
barrées, marques d'interface) restent distincts ; (3) variantes
typographiques d'un même signe, déclarées dans le seul glyphe.py. Restent
distincts, car graphémiques au niveau 2 : ſ/s, ⸗/-, uͤ/ü/ů, ꝛ/r, blancs.
L'adjudication compare aussi dans cette vue (un verdict qui ne diffère que
par le codage n'est pas un renversement) ; BBVLM_VUE_ADJ=diplo rend l'ancien
calcul.
Bogue trouvé en chemin : bilan_adj rangeait les corrections sous le texte brut
et les cherchait sous le texte normalisé ; une ligne à ligature ou à ñ perdait
sa correction pourtant validée par deux arbitres (berirev « Fiir » → « Für »).
Corrigé (clé dans la vue).
Mesure (sorties finales, référence adjugée A2, 34 pages) : **261 → 213**
éditions (−18 %), aucune page en hausse ; AmmoLIBR 11 → **0** (8 pages à 0),
busmexpo 14 → 2, herrkurt 40 → 28, culmsent 7 → 1, AphoqvSuS 6 → 2 ;
21 pages sur 34 à ≤ 2 éditions. Lecture A seule (39 pages) : 334 → 286,
6 → 7 pages à 0.
Ce qui reste (132 écarts sur lignes appariées) : conventions de la VT non
homogènes (blancs 24, ⸗/- 17, « ii » pour uͤ 10 sur buchdas), signes
monétaires lus en lettres (herrkurt 12), point médian lu « . » (8), et de
vraies fautes de lecture (ſ/f, n/u, chiffres ; ≈ 40).

## G04 (banc ALTO) — 2026-09-29 — en cours

Texte+IoU80, 36 pages : 28,551 → **29,805** ; 26 pages en hausse (hackherz
0,568 → 0,799, buchdas +0,14, herbdulc +0,14, baltdiss +0,12), 5 en baisse
(culmsent 0,809 → 0,711, busmexpo −0,03, heptaldai −0,025, 730277879 −0,02).
culmsent : boîtes de ligne meilleures (haut 0 px de la VT au lieu de −4) mais
hauts de mots 6 px trop bas. Variante avec marge verticale (BBVLM_G04_PAD)
préparée, non mesurée. G04 reste désactivé par défaut.

## G04 (décision) — 2026-09-29 — adopté pour la boîte de ligne publiée, rejeté pour les boîtes de mots

Bancs ALTO (texte+IoU80, 36 pages ; G03 seul : 28,551, pire page heptaldai 0,418) :
- G04 (majorité de l'encre dans le polygone) : 29,805 ; heptaldai 0,393,
  culmsent 0,711 ;
- G04b (retirée seulement si la majorité est dans le polygone d'une AUTRE
  ligne ; accents et points restent) : 29,800 ; culmsent 0,717 — les accents
  n'étaient pas la cause ;
- marge verticale 5 % / 10 % (4 pages) : 3,284 / 2,980 contre 3,266 — compromis ;
- hybride (G04b seulement si le haut ou le bas bouge ≥ T·h) : T 0,10 → 29,464
  (heptaldai 0,393) ; T 0,15 → 28,987 (heptaldai 0,418, culmsent 0,773).
Diagnostic culmsent : 24 mots passent sous 0,8 pour 3-8 px dans les deux sens ;
le calcul des mots (Route) est calé sur la boîte G03 et sensible à la boîte de
ligne sur les petites lignes (36 px). Toutes les variantes font reculer le
pire cas ou une page : refusé pour les mots (clause du pire cas, CRITERE.md).
Mais la boîte de ligne G04b est meilleure sur 36/36 pages (IoU médian de ligne,
somme 32,22 → 34,50 ; pire 0,758 → 0,809). Adopté pour la géométrie publiée des
TextLine (serre.py écrit `bbox` G03 pour les mots et `bbox_g04` pour la ligne ;
vers_alto : BBVLM_LIGNE_G04=0 pour l'ancien). Boîtes de mots strictement
inchangées (0/1195 différentes). Piste : recaler le calcul des mots sur la
boîte G04b.

## M01 — 2026-09-29 — rattacher les signes suscrits à leur lettre dans le filtre de composantes — rejeté

Cause identifiée de la sensibilité du calcul des mots à la boîte de ligne :
`connexe` garde une composante si son centre est à < 0,45·h du centre de la
boîte ; trop haute (G03 sur hackherz), elle garde les jambages de la ligne du
dessus ; serrée (G04b), elle perd des signes hauts. M01 (`satellites.py`) :
composante rejetée rendue à la ligne si petite (≤ 0,5 h), au-dessus du centre,
posée sur une composante gardée à ≤ 0,35 h. Texte+IoU80, 3 pages :
culmsent G03 0,809 / +sat 0,717 / G04b 0,717 / G04b+sat 0,706 ;
hackherz 0,568 / **0,174** / 0,791 / 0,641 ; heptaldai 0,418 / 0,398 / 0,403 / 0,393.
La règle attache aussi des lettres entières de la ligne du dessus (petites,
posées sur nos hampes) : trop large. Et culmsent recule même avec G03 : les
signes suscrits ne sont pas la seule cause de sa régression sous G04b.
Non adopté (BBVLM_SAT reste à 0). La boîte G04b reste réservée à la ligne publiée.

## H01 — 2026-09-29 — pages penchées : bas des mots pris sur la bande pleine — adopté

Pire page ALTO : heptaldai 0,418 (texte+IoU80). Diagnostic : bas des mots 6-9 px
trop haut, même pour les mots courts — B04 calcule les mots sur la bande
redressée réduite de la dérive (« hauteur réelle du corps »), ce qui ampute
les jambages. Bande pleine (BBVLM_REDRESSE_PLEIN) : bas juste mais encre
voisine, découpage horizontal dégradé (76 mots justes / 201, contre 84).
H01 : découpage horizontal et haut sur la bande réduite, bas sur la bande
pleine. heptaldai (mots justes et IoU ≥ 0,8) : 84 → 109 (haut aussi sur bande
pleine) → **137** (haut réduit, bas plein).
Banc 36 pages (seules les pages penchées changent, 9) : 28,776 → **29,103** ;
pire cas 0,418 → **0,568** (la pire page devient hackherz) ; heptaldai 0,682,
culmsent 0,809 → 0,851, 730277879 +0,014 ; reculs d'un mot : extraudeu
−0,007, emmeprac −0,007. Adopté (défaut ; BBVLM_REDRESSE_HYB=0 pour B04 seul).

## G05 — 2026-09-29 — boîte G04b pour les mots, décidée par page — adopté (seuil à valider sur pages neuves)

Suite de G04 : la boîte G04b fait gagner les mots là où l'encre des lignes
voisines entrait dans la boîte G03, et perdre ailleurs (calcul des mots calé
sur G03). Comme pour B04, décision par PAGE : si la boîte G04b abaisse le haut
des lignes d'au moins 5 % de h en médiane, la page est contaminée → mots sur
G04b. Seuil choisi APRÈS avoir vu les résultats G04 (culmsent, heptaldai,
busmexpo, médiane 0-3 % ; pages gagnantes ≥ 5 %) : à valider sur des pages
neuves. Pages basculées : 11/36.
Banc 36 pages (texte+IoU80, H01 actif) : 29,103 → **29,991** ; pire cas
0,568 → **0,665** ; hackherz 0,568 → 0,791, baltdiss +0,113, baurodwe +0,108,
herbdulc +0,117, aepidisp +0,088, DasWeL +0,076, herrkurt +0,075 ; un recul :
730277879 0,838 → 0,817. Défaut : BBVLM_MOTS_G04=page (0 : G03, 1 : G04b partout).

## O16 — 2026-09-29 — validation sur 4 pages neuves : N01, G05 confirmés ; chiamerk parfaite

Détail : o16/RESULTATS.md. Tirage O03 épuisé : œuvres déjà vues d'astra, jamais
de cette boucle. Texte final (glyphe) : chiamerk **0**, briedefra 1,
erasexom 4 (31 en diplo : N01 retire 27 éditions de pur codage), brieetli 8.
Aucune page ne monte avec N01. ALTO : G05 +0,100 (briedefra 0,828 → 0,919),
aucun recul ; H01 et S08 sans objet sur ces pages. CRITERE ✓ chiamerk,
brieetli. **chiamerk : 4ᵉ page parfaite de bout en bout.** Correctif associé :
la vue `norm` englobe désormais `glyphe` (elle restait sur diplo : erasexom
19 en norm contre 4 en glyphe).
O16 (suite) : recherche 0,92-0,99 ; OLR rôles 0,95-1,0. Échecs CRITERE
d'erasexom = découpage des mots de la VT (blancs collés/coupés, corrigés par
les arbitres dans la référence adjugée) ; restes texte = ambiguïtés réelles
(uͤ/ü, J/I, ß/ſſ, coquille VT).

## V02 — 2026-09-29 — une lecture ou deux ? (vue glyphe, 38 pages adjugées)

Lecture A seule (p2, sans I01) 284 éditions, 7 pages à 0 ; lecture B seule
272, 8 ; chaîne complète (A+B+arbitre P3+I01) **226**, 9 à 0 ; pire page 41
(A) contre 43 (qualité : herrkurt/extraudeu, difficultés non liées au nombre
de lectures). Gain concentré sur 10 pages (≥ 3 éd.) : 730277879 18 → 0,
herrleyc 20 → 8 et herbdulc 10 → 4 (en partie I01, gardé par le mode économe),
cingdei 16 → 13, DasWeL 13 → 10. Coût : ≈ 2 appels VLM de plus par page.
Aucun signal a priori connu ne désigne ces pages (Tesseract réfuté, T01) :
le mode qualité reste le défaut pour une VT, le mode économe (−50 % de
lecture, +25 % d'éditions) pour l'indexation.

## O16-S — 2026-09-29 — Sonnet comme second lecteur — rejeté (sans arbitrage)

Protocole o16/PROTOCOLE_S.md (figé avant lecture). Mêmes 4 pages, même
consigne, mêmes images. Lecture seule contre référence adjugée (glyphe) :
Sonnet 6 / 4 / 17 / 20 (chiamerk, briedefra, erasexom, brieetli ; total 47)
contre Opus B 0 / 1 / 8 / 9 (18). Lignes en désaccord avec A (à arbitrer) :
Opus+Sonnet 4 / 3 / 18 / 11 (36) contre Opus+Opus 0 / 0 / 4 / 3 (7) — cinq
fois plus de travail d'arbitre. Durée de lecture Sonnet 50-380 s contre
40-60 s pour Opus, jetons plus nombreux. L'économie visée n'existe pas :
arbitrage non lancé (il coûterait plus que la seconde lecture Opus).
Le second lecteur reste Opus.

## M-meta — 2026-09-29 — métadonnées : source de vérité identifiée, toujours bloquée

Dépôt OCR-D-GT-VD-SBB : MODS vides (vérifié), METADATA.yml et README sans
métadonnée par œuvre. Source existante : export CSV des métadonnées METS/MODS
des 206 411 œuvres numérisées de la SBB (Stabi Lab, lab.sbb.berlin/datadumps ;
Zenodo). Hôtes testés et refusés par la politique réseau : sru.k10plus.de,
unapi.k10plus.de, content.staatsbibliothek-berlin.de,
digital.staatsbibliothek-berlin.de, oai.sbb.berlin, lab.sbb.berlin,
zenodo.org, huggingface.co. Il suffirait d'autoriser lab.sbb.berlin (ou
zenodo.org) pour disposer d'une VT de métadonnées (titre, auteur, lieu, date,
imprimeur) sur les 67 œuvres.

## C-balayage 2 — 2026-09-29 — CRITERE sur 40 pages, chaîne actuelle

CRITERE (e01, lignes kraken appariées à la VT) avec le calcul des mots de la
chaîne (G05 : boîte G04b sur pages contaminées ; B04 + H01 sur pages
penchées) : **16/40** ; avec Route sur G03 (ancien) : 14/40. Gagnées :
heptaldai (H01) et briedefra (G05) ; aucune perdue. ✓ : albedm, culmsent,
AmmoLIBR, backhart, heptaldai, branchri, erobdefoa, bankgraf, caladr,
aepidisp, baurodwe, dalarie, busmexpo, briedefra, brieetli, chiamerk.
Échecs restants : surtout « lignes en échec » (nombre de mots ≠ VT : blancs
de la VT ou du texte lu, 18 pages) ; frontières hors seuil : herrkurt (89,8 %),
herrleyc, hackherz, buchdas, berirev (pire 6-11c), 730277879.
Correction de la mesure (même jour) : CRITERE évaluait les lignes kraken
brutes, sans la scission S08 ni la coupe des manchettes S02 que l'ALTO
applique (manchettes gauches fusionnées : buchdas pire 10,7c, berirev 7,2c,
herrleyc 5,9c — tous les mots décalés d'un cran). vers_alto expose désormais
`lignes_page()` (mêmes lignes pour l'ALTO et pour l'évaluation ; ALTO
inchangés). CRITERE avec les lignes de l'ALTO : **18/40** (herrleyc et
chridiss ✓ en plus) ; buchdas pire 10,7 → 1,4c, berirev 7,2 → 5,5c.

## C-rapport — 2026-09-29 — lignes en échec : découpage de la VT ou texte lu ?

(Rapport seulement ; CRITERE.md inchangé.) Une ligne est « en échec » si
notre nombre de mots diffère de celui de la VT. Sur 41 telles lignes (40
pages, lignes appariées) : **25** portent un texte identique à la référence
adjugée (vue glyphe) — la VT colle ou coupe des mots que les deux arbitres
ont corrigés (erasexom 7, hackherz 4…) — et 16 viennent de notre texte
(blancs ou mots faux). CRITERE « hors découpage VT » (comme A3 pour le texte) :
**20/40** (baltdiss, cingdei en plus des 18). Les deux chiffres sont rapportés.

## R-balayage — 2026-09-29 — recherche (ALTO, mot + boîte) sur 40 pages, chaîne actuelle

Rappel médian **0,956** ; 20/40 pages ≥ 0,95 ; pire 852691769 0,767 / 0,761
(table des matières à numéros alignés à droite et texte vertical, lignes non
trouvées par kraken), puis durrgeda 0,847 (titres d'apparat), AphoqvSuS 0,864
(grec), geomeikud 0,870 (bas-allemand), DasWeL 0,873, herrkurt 0,876,
caladr 0,879 (10 lignes : un mot manqué pèse 3 %).

## S08b — 2026-09-29 — pire page en recherche (852691769) : colonnes de renvois — non poursuivi

852691769 (rappel 0,767) : kraken fusionne chaque entrée de liste avec le
renvoi aligné à droite (« 1. Dolium … » + « 1. — 6. »), et deux titres
verticaux ne sont pas trouvés. S08 ne scinde pas : le renvoi apporte 2
caractères réduits (gain de distance 0,03-0,07 < 0,15) et il est lu loin dans
l'ordre de lecture (colonne « Varietates » après toute la liste, hors de la
portée de 6 lignes). Assouplir la longueur minimale (renvois chiffrés) : aucun
effet (banc 40 pages, 1 110/1 143 lignes trouvées, inchangé). Il faudrait une
détection de colonne alignée (taquets, L13) pour une seule page du corpus :
non poursuivi.

## EY1 (installation) — 2026-09-29

eynollah 0.9.2 tire tensorrt/onnxruntime-gpu via pypi.nvidia.com (refusé) ;
installé eynollah 0.3.1 (version des modèles v0.3.1, release GitHub, 1,9 Go)
avec tensorflow-cpu 2.15.1 et une cale d'espace de noms `qurator.eynollah`
(paquet 0.3.1 mal empaqueté). Lancement sur les 8 pages du protocole.

## EY1 — 2026-09-29 — Eynollah pour les lignes manquées par kraken — rejeté

Protocole o16/PROTOCOLE_EYN.md. Lignes VT trouvées (IoU ≥ 0,5), chaîne →
+ lignes eynollah sans recouvrement kraken : extraudeu 19 → 21, chiamerk,
eberbrev, erasexom 28-29 → +1, herbdulc 39 → 40, durrgeda 18 → 19 (mais 10
lignes ajoutées, précision 0,62 → 0,49), 852691769 71 → 71 (9 ajoutées,
aucune utile), témoin erobdefoa 34 → 34 (1 parasite). ALTO texte+IoU80
(8 pages) : 6,659 → 6,664 (chiamerk +0,005 seul) ; pire page inchangée
(852691769 0,673). Les lignes retrouvées ne reçoivent presque jamais de
texte : l'ancrage S05 a déjà placé les lignes lues ailleurs, ou les lignes
manquées sont des titres d'apparat que l'ancrage ne relie pas. Coût : modèles
1,9 Go, TensorFlow, ≈ 1 min/page sur CPU. Non adopté (BBVLM_EYN reste à 0).

## I02 — 2026-09-29 — signe d'inflexion par mot (verdict de l'arbitre I01 appliqué au mot) — rejeté

brieetli (O16) mêle e suscrit et deux points ; I01 (décision de page, ≥ 3
votes et 3/4 d'accord) s'abstient, alors que l'arbitre a vu « points » sur
deux des trois mots fautifs. I02 : chaque mot examiné reçoit le signe vu par
l'arbitre, à toutes ses occurrences (BBVLM_I02). 21 pages avec verdicts I01,
vue glyphe : 166 → 172 éditions ; herrleyc 8 → 4, brieetli 8 → 4, mais
extraudeu 43 → 47 et chiamerk 0 → **10** (un verdict par mot erroné propagé à
toutes les occurrences). Le verdict d'un arbitre sur un mot n'est pas assez
sûr seul — c'est la raison de la garde d'I01. Non adopté (BBVLM_I02 = 0).
Note I01/chiamerk : l'arbitre voit un « anneau » sur 5 mots, la VT code
U+E72B (u + e suscrit) : dans cette impression tardive, le e suscrit est un
petit rond. La garde d'I01 (≥ 3 votes sur mots à inflexion) s'abstient
(2 votes : « wůr⸗ » coupé et « Fůße », « demůthigen » hors lexique R2) — et
la page reste à 0. Forme et convention peuvent diverger : un « anneau » vu
n'implique pas ů dans la VT.

## O17 — 2026-09-29 — chaîne gelée sur les 4 dernières œuvres

Détail o17/RESULTATS.md. Texte (glyphe) : ferrepit **0** (10e page à 0),
canitrac 4 (0 en norm), 688357687 7, hermhyst 23 (page de 150 car. ; deux
lignes côte à côte fusionnées par les lecteurs). Lecture A seule = chaîne
complète sur les 4 pages. ALTO 0,54-0,84 ; CRITERE 0/4, seuils manqués de peu
sauf hermhyst ; recherche 0,94-0,98 hors hermhyst (0,57). G05 et S08 sans
effet, H01 +0,007. Aucun réglage fait après lecture.
Incident : première vague de lectures perdue (limite de session de l'API),
relancée à l'identique après réinitialisation.
O17 (diagnostic ALTO) : 688357687 (0,713) et canitrac (0,739) ont un texte
presque juste ; les mots entre IoU 0,5 et 0,8 n'ont aucun écart vertical,
seulement des bords gauche/droit décalés (médiane 4-9 px) sans cause commune
(coupe dans le mot voisin « Ioan. | And. » 19 px ; début de ligne 5-12 px).
Les frontières restent justes au caractère près (688357687 : 97,2 % ≤ 0,5c) :
le seuil IoU 0,8 est sévère pour les mots courts. Pas de correctif systématique.

## V03 — 2026-09-29 — seconde lecture sur signal de page (écart lecture A ↔ Tesseract) — réfuté

Question : peut-on ne relire que les pages où la seconde lecture gagne ? Signal
sans VLM : distance d'édition moyenne (appariement hongrois) entre les lignes
de la lecture A et l'OCR Tesseract des lignes kraken (cache S05). 42 pages
adjugées, vue glyphe. Gain de la chaîne complète sur A seule : 58 éditions,
concentré (730277879 +18, herrleyc +12, herbdulc +6). Spearman(gain, distance)
= **−0,11** (p 0,48). Relire les 5 / 10 / 20 pages les plus distantes capte
4 / 1 / 12 éd. sur 58. Les pages qui gagnent le plus sont parmi les plus
proches de Tesseract (erreurs fines : signe suscrit, lettre, pas de ligne
ratée). Comme T01 (ligne), le signal de page Tesseract est réfuté. Le mode
qualité reste le défaut ; aucun critère a priori ne remplace la seconde lecture.

## Bilan texte — 2026-09-29 — 42 pages adjugées, chaîne gelée, vue glyphe

10 pages à 0 ; 18 ≤ 1 ; 24 ≤ 2 ; 28 ≤ 5 ; 36 ≤ 10 ; médiane 2 éditions par
page ; CER global 0,50 % (260 éd. / 51 896 car.). Pires pages : extraudeu 43
(ligne double à lettrine, L08), buchdas 37 (VT « ii » pour uͤ, lignes
indécidées), herrkurt 28 (signes monétaires lus en lettres), hermhyst 23
(page de 150 car., lignes côte à côte fusionnées).

## W01 — 2026-09-29 — bords de mots pris chez Tesseract (ancrage au mot) — rejeté

Tesseract (psm 7, TSV) donne une boîte par mot ; les mots lus appariés à un
mot Tesseract (distance normalisée ≤ 0,34, alignement monotone) prennent ses
bords gauche/droit, la hauteur reste celle du calcul connexe. 4 pages
(texte+IoU80) : culmsent 0,851 → 0,680, hackherz 0,791 → 0,710,
688357687 0,713 → 0,615, canitrac 0,739 → 0,723 ; somme 3,093 → 2,729.
Les boîtes de mots de Tesseract sont moins justes que les nôtres (bords
lâches, ponctuation). Premier essai invalide (config « tsv » absente de
notre tessdata : aucune boîte lue, scores identiques) — corrigé avant la
mesure ci-dessus. Non adopté (BBVLM_W01 = 0).

## OLR-balayage — 2026-09-29 — rôles, régions, ordre (lecture A) sur 44 pages

Toutes pages (O07-O17) : rôles médiane 1,000 (35/44 ≥ 0,9, pire durrgeda
0,364) ; F1 régions médiane 0,992 (31/44, pire culmsent 0,032) ; ordre
médiane 0,987 (40/44, pire busmexpo 0,833). Les pires F1 d'O07 (une seule
région : consigne sans régions) et d'O08 culmsent (33 régions lues pour 8 :
liste d'items découpée ligne à ligne, avant la règle « une liste reste une
région » de P5) ne mesurent pas la consigne actuelle. Restes sous 0,9 avec la
consigne P6 : 852691769 (tableau, 48 régions VT), durrgeda (page de titre),
hermhyst (chanson), brieetli, briedefra, caladr, dalarie.

## V04 — 2026-09-29 — coût des modes de lecture sur 42 pages (vue glyphe)

Lecture A seule : 318 éd., 8 pages à 0 (1 appel VLM) ; mode économe (A + I01,
signe d'inflexion appliqué à A) : 300 éd., 8 à 0 (1 appel + 1 si signes sur u) ;
mode qualité (A + B + arbitre P3 + I01) : **260** éd., 10 à 0 (3 appels).
Le mode qualité retire 13 % des éditions du mode économe pour ≈ 1,5 appel de
plus par page. Aucun signal a priori ne désigne les pages qui en profitent
(T01 ligne, V03 page). Recommandation inchangée : qualité pour produire une
VT, économe pour indexer.

## R01 — 2026-09-29 — reproductibilité de bout en bout (dossier vierge)

Rejeu de chiamerk (O16) à partir de page.png seule + les deux lectures + les
verdicts VLM, dans un dossier neuf : `chaine.py prepare → arbitrage → final`.
Défaut trouvé : la page réduite et les bandes vues par les lecteurs n'étaient
produites que par prep_sbb.py (qui télécharge aussi la VT) ; une image seule
ne donnait que les zooms. Corrigé : `vues_zoom.vues_base()` les tire de
page.png (mêmes paramètres) quand elles manquent. Résultat : les 16 vues
identiques octet pour octet ; tâches P3 et I01 identiques ; texte final
identique ; ALTO identique (hors nom de fichier et date). Le premier
`prepare` avait échoué une fois sans message (segmentation kraken hors délai
de la commande) ; le second a réussi en 27 s.

## ALTO régénérés — 2026-09-30 — chaîne actuelle sur 44 pages

Tous les ALTO refaits avec la chaîne gelée (S08, S02, G05, H01, G04b publiée).
Lignes lues non placées : 26 → **19** sur 1 390 (1,4 %) ; restes : emmeprac 6
(numéros en marge « 46 », « 47 »…), berirev 3, AphoqvSuS 2, canitrac 2, six
pages à 1. Les ALTO archivés du dépôt (oNN/alto/) sont remplacés par ces
versions.

## S06b — 2026-09-30 — bandes de projection comme lignes candidates — rejeté

But : placer les 19 lignes lues sans ligne kraken (numéros en marge
d'emmeprac, bouts de manchettes). Les bandes d'encre hors lignes kraken
(`bandes.py`, L11) sont ajoutées comme candidates ; l'ancrage S05 ne leur
donne du texte que si une ligne lue y correspond. 4 pages à lignes non
placées (texte+IoU80) : AphoqvSuS 0,788 → 0,780, berirev, emmeprac,
canitrac inchangées ; somme 3,153 → 3,145. Les bandes ne recouvrent pas les
petits numéros (seuils de taille de la projection) ou reçoivent une ligne à
tort. Non adopté (BBVLM_S06 = 0).

## Seg-balayage — 2026-09-30 — lignes publiées (ALTO) contre VT, 44 pages

Rappel des lignes (IoU ≥ 0,5) médian 0,968, 27/44 ≥ 0,95, pire hermhyst 0,78 ;
IoU médian des lignes 0,962 (pire chridiss 0,81) ; précision médiane 1,00
(pire 0,82). Rappel moyen 0,952.

## D-mots — 2026-09-30 — bord droit des mots par type de fin (44 pages, ALTO régénérés)

Hypothèse tirée d'O17 (canitrac « condem- » +55 px) : les mots finis par un
trait d'union ou une ponctuation auraient un bord droit biaisé. Mesure sur
les mots appariés (IoU ≥ 0,3) : écart du bord droit (nous − VT) / hauteur,
médiane +0,00 (trait, n 317), +0,00 (ponctuation, n 2 005), −0,01 (autres,
n 6 472) ; IoU ≥ 0,8 pour 91 %, 87 %, 88 %. Aucun biais : le cas canitrac est
isolé. Pas de correctif.

## S08c — renvois chiffrés alignés à droite (tables) — ADOPTÉ (30/09, 02h50 Paris)
- Hypothèse : sur 852691769 (pire retrieval, 0,767), kraken colle au texte la colonne de renvois « 1. — 6. » ; la détacher donnerait une ligne candidate à l'ancrage S05. Littérature : L17.
- v0 (blanc d'encre ≥ 0,6 h dans le quart droit) : aucune coupe — les blancs internes du renvoi (22–31 px) valent celui qui le sépare du texte. Négatif, abandonné.
- v1 (boîtes de mots Tesseract, psm 7 : suite finale de jetons chiffrés commençant après la moitié de la ligne) : 43 pages, 3 gains, 1 perte (briedefra 0,919 → 0,909 : prose « … Beſatzung aus 500 » coupée).
- v2 (+ garde-fou : chiffres de la suite = chiffres d'une ligne purement chiffrée de la lecture ; ne peut que retirer des coupes de v1) : rappel texte+IoU80 852691769 0,673 → 0,681, canitrac 0,739 → 0,749, emmeprac 0,762 → 0,769, briedefra 0,919 = ; 39 autres pages inchangées ; pire cas 0,536 inchangé. Retrieval 852691769 : rappel 0,767 → 0,786, précision 0,761 → 0,780.
- Décision : adopté par défaut (BBVLM_RENVOIS=1). Gain faible : la plupart des renvois de 852691769 restent sans ligne kraken (lignes non trouvées, pas collées).
- v3 (30/09, 03h05 Paris) : la page 852691769 est déclarée « romain » → Tesseract `lat` lit « 1. » « j. » et le garde-fou refuse la coupe. Les deux modèles sont maintenant essayés (celui de l'écriture d'abord). Banc 44 pages contre RENVOIS=0 : 852691769 0,673 → 0,685, canitrac 0,739 → 0,749, emmeprac 0,762 → 0,771 ; 41 pages identiques ; pire cas 0,536 inchangé. Retrieval 852691769 : 0,767 → 0,786 (précision 0,780).
- Diagnostic restant sur 852691769 (46 mots IoU < 0,5) : renvois lus ancrés sur les intitulés verticaux de marge (« Claſſis I. Conchæ Univalves. », que Tesseract ne sait pas lire debout) et renvois sans ligne kraken. Texte vertical : 6 mots sur tout le corpus (une seule page) → module de rotation (L18) non prioritaire.

## S09 — lignes courtes complétées par l'encre — ADOPTÉ (30/09, 04h00 Paris)
- Diagnostic CRITERE (44 pages, 18 ✓) : les échecs viennent de (a) lignes de référence sans ligne kraken appariée — lignes courtes à éléments espacés que kraken ne voit qu'en fragment (« ) 152 ( » → « 152 », « j. Jsop », « §.VI. », « II. ») ou fusionne dans une ligne longue (« Gal. V. », « Kinder. ») — et (b) nombre de mots lu ≠ VT (28 lignes / 1265 pour les seuls blancs). Kraken brut montre déjà les fragments : ce n'est pas le resserrage G03. Littérature : L19 (lignes courtes manquées, défaut connu).
- Règle (`etend.py`) : ligne de largeur < 6 h ; ajout de proche en proche des composantes dont le centre est dans la bande, hauteur 0,35–1,6 h, rapport h/l ≤ 4, écart ≤ 2 h, ne touchant aucune autre ligne ; la boîte étendue ne doit chevaucher aucune autre ligne de sa bande ; G04b ne reçoit que l'extension horizontale.
- Itérations (4 puis 7 pages, puis 44) : v0 hackherz 0,791 → 0,560 (lignes de la page d'en face prolongées par le filet de reliure jusque dans le texte ; puis G05 désactivé parce que bbox_g04 = bbox) → garde-fous bande + forme + G04b horizontal. v1 dalarie −0,007 (tiret ornemental de « — 14 — » absorbé) → hauteur ≥ 0,35 h (0,4 perd extraudeu). Garde-fou par relecture Tesseract (extension gardée si elle rapproche d'une ligne lue) : essayé en 3 variantes, trop bruité (refuse EXTRACT, garde des fausses extensions selon le modèle) → retiré.
- Résultat (texte + IoU80, 44 pages) : extraudeu 0,814 → 0,862, caladr 0,697 → 0,727, 730277879 0,817 → 0,824, erobdefoa 0,979 → 0,983, emmeprac 0,771 → 0,774 ; perte 688357687 0,713 → 0,707 (fragments d'en-tête sans référence étendus, qui attirent à l'ancrage S05 deux lignes lues bien placées ailleurs) ; 38 pages identiques ; pire cas 0,536 inchangé.
- CRITERE : 18/44 = ; 730277879 lignes en échec 1 → 0, 852691769 7 → 6, extraudeu frontières ≤ 0,5c 96,3 → 99,1 %, pire 1,52 → 0,54 c ; aucune page dégradée.
- Décision : adopté par défaut (BBVLM_ETEND=1). Reste : lignes courtes fusionnées dans une ligne longue (type « Gal. V. », AphoqvSuS, berirev) — relève d'une scission, pas d'une extension.

## S02c — manchettes collées, pages sans rôles OLR — ADOPTÉ (30/09, 04h30 Paris)
- Diagnostic : AphoqvSuS (lecture sans rôles) a « Gal. V. », « A. C. », « 14 » en lignes lues séparées, mais kraken les soude à la ligne du texte courant. S08 ne coupe pas (« A. C. », « 14 » < 3 caractères réduits ; « Gal. V. » collé à une ligne grecque que la réduction a-z0-9 vide) ; S02 n'est appliqué que si le lecteur signale des manchettes (fausses coupes sur vers et listes, cf. S02). Littérature : L20 (la transcription corrige la segmentation).
- Règle : sans rôles, les coupes proposées par `coupe_page` sont gardées seulement si (1) le petit morceau, relu par Tesseract (deux modèles), est à distance ≤ 0,5 d'une ligne lue et (2) le grand morceau n'est pas plus loin d'une ligne lue que la ligne entière.
- Itérations : seuil 0,34 → aucune coupe sur AphoqvSuS (Tesseract lit « Gal. V. » en italique « ff Gat, F. 0 ») ; 0,5 → AphoqvSuS +0,034 mais geomeikud 0,778 → 0,759 (« ſehr » détaché en fin de ligne, relu « fehr » ≈ ligne lue « wer ») → condition (2) ajoutée.
- Résultat (texte + IoU80, 44 pages) : AphoqvSuS 0,788 → 0,822, berirev 0,865 → 0,885 ; 42 pages identiques (dont les pages de vers brochrnx, ferrepit) ; pire cas inchangé. CRITERE 18 → **19/44** : AphoqvSuS ✓ (lignes en échec 2 → 0), berirev 2 → 1 (pire frontière 5,48 → 1,54 c) ; aucune page dégradée.
- Noté au passage (non traité, trop rare) : erreur de lecture « manchette recopiée en fin de ligne du texte courant » (berirev l. 41 « … halten. Für die würm » + l. 42 « Für die würm ») : 1 cas sûr sur tout le corpus.

## S10 — blancs de mots vérifiés par l'encre — REJETÉ (30/09, 04h45 Paris)
- Motivation : 28 lignes / 1265 diffèrent de la VT par les seuls blancs (2e cause d'échec CRITERE après les lignes sans ligne kraken : 33) ; ferrepit échoue seulement par 2 lignes de ce type. Vérifié sur l'image : « ſolib us » a un écart imprimé de 11 px, autant qu'entre deux mots (la VT diplomatique a raison, la lecture a normalisé). Littérature : L21.
- v1 (fusion si écart entre boîtes < 0,3 × écart médian ; scission si blanc interne ≥ 0,8 × médian et ≥ 1,5 × 2e blanc) sur 4 pages : CER glyphe hackherz 1 → 50, erasexom 4 → 42, ferrepit 0 → 15, AyrmThes 1 → 15 ; rappel ALTO −0,09 à −0,22. Les écarts entre boîtes de mots sont ceux du découpage de la chaîne (ponctuation collée, « pluribus. »), pas de l'encre : fusions fausses en masse.
- v2 (scission seule, blanc ≥ 1,0 × médian, lettres des deux côtés) : 7 lignes modifiées, 1 juste (« ſolib us »), 6 fausses (« m eumq », « confirme t », « Fra u », « v ielen », « ih mviel » : bon blanc, mauvaise position). CER glyphe hackherz 1 → 5, ferrepit 0 → 2, erasexom 4 → 5.
- Causes : lettres fragmentées par la binarisation (faux blancs internes) ; position du blanc dans le texte estimée au prorata de la largeur, trop imprécise. Une version viable demanderait des positions de caractères (reconnaisseur avec alignement), hors de portée ici pour un gain borné à ~1 % des lignes.
- Décision : rejeté ; `blancs.py` conservé, BBVLM_BLANCS=0 par défaut.

## S08c v4 — numéros en bout de ligne (30/09, 04h55 Paris) — ADOPTÉ
- Diagnostic des 33 lignes sans ligne kraken (chaîne S08c+S09+S02c, 25 pages ✗) : 18 fragments, 6 fusions, 5 absentes, 4 décalées. Motif récurrent : numéros alignés à droite du texte (emmeprac « 46 » « 48 » « 50 », cingdei « 64. »…, herbdulc « 54 »), soudés à la ligne ou absents.
- Pourquoi S08c v3 ne les détachait pas (emmeprac) : pré-filtre « l'OCR de ligne finit par un chiffre » raté (« 50 » lu « 5o ») ; jeton « 64^ » refusé ; « 48 » relu « 45 » ≠ ligne lue. v4 : pré-filtre retiré (largeur ≥ 6 h conservée), jeton = aucune lettre (le tiret de « 1. — 6. » reste admis ; une première version exigeant un chiffre par jeton faisait perdre 852691769), chiffres égaux à ceux d'une ligne lue à une substitution près dès 2 chiffres.
- Banc 44 pages (RENVOIS 0 contre 1, chaîne S09+S02c) : emmeprac 0,762 → 0,802 (0,774 en v3), 852691769 0,673 → 0,685, canitrac 0,739 → 0,749 ; 41 pages identiques (briedefra intact) ; pire cas inchangé.
- cingdei : les numéros « 64. » « 65. » « 66. » ne sont pas dans la lecture (manuscrits à l'encre, écartés par l'arbitre P3b, cf. P3b 28/09) — convention, cas unique, inchangé. Recherche de toutes les lignes portées par une seule lecture et perdues dans le texte final : 5 sur tout le corpus, dont 3 dans la VT (ces trois-là).

## S09b — lignes courtes : bande élargie, appartenance par le centre — ADOPTÉ (30/09, 05h15 Paris)
- Fragments restants après S09 : « K 2 », « B 5 » (signatures : boîte kraken minuscule, 20 px, décalée → le centre du « K » hors bande), « §.VI. » (le « § » touche la boîte de la ligne voisine, les boîtes kraken se chevauchant par les jambages → exclu par « ne touche aucune autre ligne »).
- Règle : bande verticale = centre de la boîte ± max(h, hm)/2 ; une composante appartient à une autre ligne seulement si son centre est dans la boîte de celle-ci.
- Banc 44 pages (S09 contre S09b) : euanaua 0,837 → 0,859, eberbrev 0,818 → 0,830, berirev 0,885 → 0,897, erasexom 0,778 → 0,786 ; 40 pages identiques ; aucune perte.
- CRITERE 19 → **21/44** : berirev ✓ (1 → 0 ligne en échec), eberbrev ✓ (1 → 0), erasexom 9 → 8 ; aucune page dégradée.
- CRITERE avec S08c v4 seul (avant S09b) : 19/44, identique à S02c.
- Frontières (730277879 92,7 %, canitrac 94,5 %) examinées : boîtes prédites contiguës (aucun blanc trouvé, coupe proportionnelle). 730277879 : tiret « — » soudé aux mots voisins (« beſtimmt.—Man ») que la VT sépare en trois mots ; canitrac : croix « † » en tête de ligne, comptée comme mot, absente du masque → tous les mots décalés d'un cran. Cas typographiques isolés, au cœur du boxer (Compose) ; notés, non traités.

## G06 — boîte G04b pour les mots, choisie ligne par ligne — REJETÉ (30/09, 05h22 Paris)
- Piste listée dans ETAT (« recaler le calcul des mots sur G04b partout ») : G05 choisit la boîte G04b pour toute la page si le haut des lignes descend en médiane de ≥ 0,05 h ; G06 applique le même seuil à chaque ligne (BBVLM_MOTS_G04=ligne).
- Banc arrêté à 11 pages (texte + IoU80, G05 contre G06) : gains AphoqvSuS +0,009, geomeikud +0,009, backhart +0,007 ; pertes culmsent 0,851 → 0,773, hackherz −0,011, herrleyc −0,011, berirev −0,004. Le choix par page (G05) est plus sûr : une décision ligne à ligne suit le bruit du resserrage.
- Décision : rejeté, mode laissé en option.

## Inventaire des fautes de texte restantes (30/09, 05h30 Paris) — diagnostic
- 42 pages adjugées, vue glyphe, 260 éditions. Classes : blancs 25 (15 manquants, 10 en trop) ; « ⸗ »/« - » 18 ; « ii » (VT) ↔ « uͤ » 9 (graphie de la VT, berirev) ; signes monétaires PUA U+F2E8/U+F2E9 lus « fk »/« gK » 12 (herrkurt seul, cas P6 connu) ; ſ/s/ß/f 16 ; points et ponctuation ~12 ; le reste en unités.
- « ⸗ »/« - » : deux pages, sens opposés — eberbrev (romain) VT 13 « ⸗ », lecture 13 « - » ; heptaldai (Fraktur) VT 3 « - », lecture 3 « ⸗ » ; cingdei 1. Pas de règle par écriture possible sans contredire l'une des deux ; image trop peu nette à la coupure pour trancher. Conventions de transcription propres à chaque œuvre.
- Conclusion : aucune classe restante n'est à la fois fréquente, homogène et corrigeable par règle ; les blancs (S10) ont été essayés et rejetés.

## ALTO régénérés avec la chaîne gelée (30/09, 05h35 Paris)
Chaîne : S08 + S08c v4 + S09b + S02/S02c + G05 + H01 + G04b publiée. Lignes lues non placées : 19 → **7** sur 1 390 (DasWeL, AmmoLIBR, durrgeda, emmeprac, herbdulc, AyrmThes, chiamerk : 1 chacune). 40 ALTO archivés (oNN/alto/) remplacés, 40/40 valides XSD 4.4. Retrieval sur 44 pages : rappel médian 0,957, 24 ≥ 0,95 ; pires hermhyst 0,57 (O17, chanson), 852691769 0,79, durrgeda 0,85.

## hermhyst — pire retrieval (0,57) : paroles sous portées (30/09, 05h40 Paris) — diagnostic
Page de chant (O17) : paroles imprimées sous deux portées, syllabes espacées selon les notes (« din gen/ », « ſin gen/ », « Baby lon »). La VT recolle les syllabes (« dingen/ »), comme la lecture : le texte concorde. L'échec est géométrique : le boxer prend le blanc intersyllabique pour une frontière de mot (le nombre de mots étant connu, il choisit les plus grands blancs) ; « zu Babylon » et « Die zuͤchtige Su⸗ » sont deux lignes de la VT sur la même ligne de base (fusionnées par les deux lecteurs, déjà noté en O17). Genre unique dans le corpus (1 page) → non traité.

## O18 — validation sur pages neuves des règles de la nuit (30/09, 06h00 Paris) — HYPOTHÈSE TENUE
Protocole figé avant lecture (o18/PROTOCOLE.md, commit caec964) : aucune œuvre inédite ne restant, 4 pages jamais lues d'œuvres déjà vues (tirage sha256("O18"+œuvre) ; humbphys/306, planche, remplacée par herrleyc/44). Chaîne complète : 2 lectures Opus P6, arbitre P3+I01, ALTO ; référence adjugée par 2 arbitres aveugles (A2).
- Texte (glyphe) : brieetli 0, brochrnx 1, herrleyc 2, geomeikud 4 (lecture A seule : 0, 1, 4, 18).
- ALTO texte+IoU80 sans → avec les règles de la nuit : brochrnx 0,955 → 0,970, les 3 autres identiques ; CRITERE identique (2/4 : brochrnx, herrleyc) ; pire 0,816 inchangé. Aucune régression sur pages neuves : S02c, S08c v4, S09b confirmés.
- Recherche : 0,91-0,99 ; 1 ligne lue non placée sur 108. Détail : o18/RESULTATS.md.

## S11 — deux lignes kraken pour une seule ligne lue : fusion guidée par le texte — ADOPTÉ (30/09, 06h20 Paris)
- Origine : O18 geomeikud/37, 7 lignes en échec. Listes « ix.      Bonen » : kraken trouve bien « ix. » mais comme une ligne à part ; la VT et la lecture n'en font qu'une. S09c (extension à 4 h, validée par relecture) n'y pouvait rien — rejeté, laissé en option (BBVLM_ETEND_LOIN). Littérature : L20 (la transcription corrige la sur- comme la sous-segmentation).
- Règle (`scinde.fusionne`, inverse de S08) : deux boîtes voisines de la même bande (recouvrement vertical ≥ 50 %, rien entre elles) sont réunies si (a) la concaténation de leurs OCR d'ancrage ressemble bien mieux à une ligne lue que chacune seule (gain ≥ 0,15, distance ≤ 0,35), ou (b) — petit morceau illisible pour Tesseract (« ix. » lu « (6 ») — la grande boîte retrouve une ligne lue privée de son premier (ou dernier) mot (distance ≤ 0,2, strictement mieux qu'avec la ligne entière) et la petite a une largeur compatible avec ce mot (rapport 0,4-2,5).
- Itérations : (a) seule → geomeikud/34 +0,009, /37 = ; + (b) avec gain ≥ 0,15 → /34 +0,028 mais /37 −0,020 (le « x. » de « x. Kichern » non réuni — préfixe d'une lettre, gain 0,125 — attire à l'ancrage S05 la ligne « Des wert bym Sicilier… ») ; (b) en amélioration stricte → /37 +0,067.
- Banc 48 pages (O07-O18) : geomeikud/37 0,816 → 0,883, geomeikud/34 0,778 → 0,815, extraudeu 0,862 → 0,897, caladr 0,727 → 0,758 ; 44 identiques ; aucune perte ; pire cas inchangé.
- CRITERE : 21/44 = (caladr ✓ frontières 95 → 100 %, geomeikud/34 2 → 1 ligne en échec) ; O18 2/4 = (geomeikud/37 7 → 3). Aucune page dégradée.
- Fragilité notée : l'ancrage S05 peut poser une longue ligne lue sur une petite boîte orpheline ; S11 en supprime une source.

## S12 — repli d'ancrage borné par la largeur — ADOPTÉ (30/09, 06h40 Paris)
- Constat (S11) : l'ancrage S05 peut poser une longue ligne lue sur une petite boîte orpheline. Mesure sur les ALTO de la chaîne : 18 lignes placées sur 1 459 ont une largeur par signe à plus d'un facteur 3 de la médiane de leur page. Trop étroites = faux placements (852691769 : intitulés verticaux et renvois sur des boîtes de 18-37 px, rapport 0,03-0,3 ; durrgeda « HERRN/ » sur 42 px ; AphoqvSuS ligne grecque sur 181 px ; 688357687 « Bk. Achter Th. ») ; trop larges = titres espacés corrects (« LIBER », « (11) », « L.S. », « ) 152 ( »).
- Règle (`ancre.aligne_ancre`, repli par largeur seulement) : une ligne lue sans ancre n'est posée sur une boîte libre que si sa largeur par signe (rapportée à la hauteur) vaut au moins le tiers de la médiane des lignes ancrées de la page ; sinon elle reste non placée (refus explicite, TAGREFS NON_PLACE).
- v1 à deux bornes : 730277879 rappel de recherche 0,930 → 0,909 (le folio espacé « ) 152 ( » refusé à tort) → borne haute retirée.
- v2 (borne basse seule), recherche sur 48 pages : aucun rappel ne baisse (médiane 0,961 des deux côtés, 29 pages ≥ 0,95) ; précision 852691769 0,780 → 0,835, AphoqvSuS 0,930 → 0,964, durrgeda 0,935 → 0,960, 688357687 0,960 → 0,971. Banc ALTO texte+IoU80 (5 pages ciblées) : identique (les lignes refusées n'étaient déjà pas justes). CRITERE non concerné (n'utilise pas l'ancrage).
- Décision : adopté par défaut (BBVLM_S12=1) — un refus vaut mieux qu'un faux placement pour la recherche et pour la relecture humaine.

## S09c — second passage d'extension jusqu'à 4 h, validé par relecture — REJETÉ (30/09, 06h45 Paris)
Visait les listes à numéro séparé (« ix.      Bonen »). Sur geomeikud/37 la vraie cause était une sur-segmentation (traitée par S11) ; sur geomeikud/34 (« j. Jsop », pas de boîte kraken pour « j. »), baltdiss, herbdulc, hackherz : aucun changement même avec les minuscules admises (hmin 0,2). Laissé en option (BBVLM_ETEND_LOIN=0).

## O19 — consigne P6c « deux blocs sur une même ligne de base = deux lignes » — NON ADOPTÉE (30/09, 07h05 Paris)
Constat : 2 fusions de lecteur sur 48 pages (extraudeu, hermhyst) ≈ 41 des 267 éditions restantes ; convention VT = OCR-D (ligne ⊂ région, L22). P6c = P6 + une phrase (règle 1). Protocole figé (o19/PROTOCOLE.md) : une lecture Opus P6c sur les 2 pages fautives + 3 témoins. Résultats (glyphe, lecture A) : extraudeu 41 → 4, hermhyst 23 → 44 (l'exemple « paroles … deux groupes » fait couper aux blancs intersyllabiques), témoins 852691769 2 → 5, emmeprac 8 → 10, canitrac 4 → 4 (écarts = variance de lecture, aucun changement de découpage). Règle d'adoption non remplie → non adoptée. Leçon de méthode : la variance d'une lecture unique (±2-3 éd./page) masque un effet limité à 2 pages ; un test futur exigera des lectures répétées. Détail : o19/RESULTATS.md.
- Piste écartée après O19 (07h10) : couper la ligne lue quand kraken voit deux blocs sur la même ligne de base (inverse de S11). extraudeu : kraken n'a qu'une boîte pour les deux blocs (rien pour couper) ; hermhyst : deux boîtes, mais c'est exactement la configuration que S11 réunit à juste titre ailleurs (« ix.      Bonen », blanc aussi large, que la VT recolle). La VT tranche par régions éditoriales, pas par la taille du blanc : aucun critère géométrique ne sépare les deux cas. Non implémenté.

## Segmentation remesurée (30/09, 07h15 Paris)
TextLine des ALTO régénérés (chaîne actuelle) contre VT, 48 pages : rappel médian 1,000 (38/48 ≥ 0,95), IoU médian 0,973, précision médiane 1,00. Avant les règles de la nuit (44 pages) : 0,968, 27/44, 0,962. Pires : hermhyst 0,78, extraudeu 0,81, durrgeda 0,82.

## K02 — kraken sur image réduite pour les caractères d'apparat — NÉGATIF (30/09, 07h20 Paris)
durrgeda (page de titre, lignes de 150-400 px) : segmentation blla à l'échelle 1 / 0,5 / 0,35 → 29 lignes et rappel 0,773 (17/22) identiques. blla renormalise la taille en interne : réduire l'entrée ne change rien. Les lignes d'apparat manquées ne se récupèrent pas par l'échelle.

## O20 — variance d'une lecture unique (30/09, 07h35 Paris)
4 lectures Opus par page sur 852691769, canitrac, emmeprac : 2/5/0/0, 4/4/4/4, **8/10/65/64** éditions (glyphe). Bruit fin ±2-3 éd., nul quand les fautes sont systématiques (canitrac) ; mais dérive d'interprétation bimodale sur emmeprac : 2 lecteurs sur 4 suppriment l'espace après les points d'abréviation (« ff.de iureiur.§.item ») contre la règle 2 de P6. La chaîne 2 lectures + arbitre y est exposée si A et B dérivent ensemble. Détail : o20/RESULTATS.md. Suite : P6d (exemple d'abréviations dans la règle 2), testé par lectures répétées.

## O21 — consigne P6d (espace après un point d'abréviation, exception des sigles) — NON ADOPTÉE, de peu (30/09, 07h50 Paris)
Deux lectures Opus P6d par page. emmeprac 13, 11 (P6 : 8, 10, 65, 64) — plus de dérive, mais le seuil figé ≤ 12 est manqué d'1 ; AyrmThes 0, 1 (P6 : 1) ; goclprop 10, 14 (P6 : 9, 10 ; +2,5 > 2). L'effet visé est obtenu (aucune dérive « ff.de », « Exerc. 107. diſt. 2. » espacé comme la VT, « v.c. » préservé) ; les écarts restants sont de la variance de lecture (tilde/macron, ligne de folio, accents). Critère figé manqué → P6 reste la consigne. À reprendre avec ≥ 4 lectures par page et par consigne si la dérive réapparaît en production. Détail : o21/RESULTATS.md.
- O21b (08h00 Paris) — 4 lectures par consigne : emmeprac P6 8/10/65/64 (moy. 36,8) contre P6d 13/11/11/8 (**10,75**, dérive 0/4 contre 2/4) ; goclprop P6 9/10/11/11 (10,25) contre P6d 10/14/10/12 (11,5, dans la tolérance +2) ; AyrmThes 1/1 contre 0/1. Critère figé rempli → **P6d ADOPTÉE** comme consigne de lecture (chaîne, arbitre P3). Les lectures déjà faites du corpus ne sont pas refaites.

## O22 — consigne P6e (deux blocs sur une même ligne = deux lignes, sans l'exemple des paroles) — ADOPTÉE (30/09, 08h15 Paris)
4 lectures Opus par page. extraudeu 1/2/0/45 (moy. 12,0 contre 41 en P6), hermhyst 23/24/25/3 (18,75 contre 23), témoin 852691769 5/3 (4,0). Les trois critères figés sont tenus. Aucune coupe aux blancs intersyllabiques (erreur de P6c corrigée). Application probabiliste (3/4 sur extraudeu, 1/4 sur hermhyst). P6e devient la consigne de lecture (chaîne, arbitre P3). Détail : o22/RESULTATS.md.

## O23 — validation P6e sur 4 pages neuves (30/09, ~09h30 Paris)
Chaîne par défaut (2 lectures Opus P6e, arbitre P3/I01, S08c/S09b/S02c/S11/S12). Texte glyphe contre l'adjugée : abdipre 0, BiedBern 1, branchri 3, caladr 1 → hypothèse tenue (médiane 1, pire 0,17 %). ALTO txt+IoU80 0,927/0,865/0,910/0,834 ; CRITERE 1/4 ; recherche rappel 0,976/0,965/0,981/0,886. **Négatif méthodologique** : contre la VT distribuée caladr compte 18 éd. ; l'imprimé porte « q́ » avec le crochet ꝫ sous la hampe (recadrage vérifié), la VT le code U+F50D, les deux lecteurs écrivent « q́ » et les deux arbitres d'adjudication valident « q́ » (8 éd., 7 lignes). Une omission réelle a donc été absorbée par la règle A2. Par ailleurs la VT code « -que » tantôt « qꝫ » tantôt « q; » (codage). Suite : T01. Détail : o23/RESULTATS.md.

## T01 — abréviation « -que » (30/09, ~10h00 Paris) — ADOPTÉE
Littérature L23 (MUFI : U+F50D = q + aigu + ꝫ ; la VT emploie aussi « q; »). T01a : vue glyphe q; ≡ qꝫ (tout signe combinant sur q admis ; la version « accent seul » faisait perdre eberbrev « deniq̄; ») ; T01b : p2, « q́ » non suivi d'une lettre ni de « ; » → U+F50D. 50 pages adjugées : total 511 → 499 éd. contre la VT, 282 → 274 contre l'adjugée ; seules canitrac (−2), abdipre (−2), caladr (−8) bougent, aucune perte. Audit aveugle (2 Opus sans candidats) des 7 lignes de caladr où l'adjudication avait validé « q́ » : les deux écrivent « q́ꝫ » → 7 verdicts annulés (adj/annule.json, support dans bilan_adj.py). La règle A2 ne protège pas d'un biais partagé lecteurs/arbitres. Détail : t01/RESULTATS.md.

## A01 — audit aveugle des verdicts d'adjudication (30/09, ~10h35 Paris) — hypothèse réfutée
97 lignes où l'adjudication avait changé la VT (12 œuvres à écart > 5 éd.), 2 relecteurs Opus aveugles par ligne, sans candidats. Confirmés 56, indécis 33, **annulés 8 (8,2 % > 5 % prévus)** : surtout des blancs (6), plus ſteis/ſtets, un renvoi de colonne, uͤ/ů. Mesure contre l'adjugée auditée : 274 → 283 éd., pages à 0 : 12 → 10, pire inchangé (extraudeu 43). L'audit devient obligatoire (ETAT, règle 4). Détail : a01/RESULTATS.md.

## A01b — audit aveugle du reste des verdicts (30/09, ~10h55 Paris) — hypothèse tenue
90 lignes, 31 pages, même règle qu'A01. Confirmés 54, indécis 32, annulés 4 (4,4 %) : blancs/ponctuation (extraudeu ×2, bankgraf) et canitrac « pleriq; » (accent perdu). Total contre l'adjugée auditée 283 → 281 ; pages à 0 : 11/50 ; pire extraudeu 42. Toutes les références adjugées sont désormais auditées. Détail : a01b/RESULTATS.md.

## Inventaire des 281 éd. restantes (30/09, ~11h05 Paris, CPU)
Référence adjugée auditée, vue glyphe, par opération d'édition : lettre 109, inflexion 49, lignes manquantes/en trop 42, blancs 26, ponctuation 25, coupure 18, ſ/s 7, J/I 5. Concentrations : extraudeu (lignes fusionnées, lecture antérieure à P6e), buchdas (VT « ii » pour uͤ ×10 lignes — faute de la VT que les deux arbitres rejettent sans s'accorder sur ü/uͤ, donc gardée par A2 ; points médians « ·xvij· » lus « . xvij. », 12 éd., seule page des 76 VT à en avoir), herrkurt (lecture antérieure aux jetons {florin}/{groschen} de P6 : « fk »/« gK » au lieu de U+F2E8/F2E9), eberbrev (⸗/- 13). Pas de nouvelle règle générale justifiée par ces restes : ce sont soit des lectures archivées antérieures aux consignes actuelles, soit des fautes de VT non tranchées (A3), soit des traits propres à une seule page.

## C02 / C02b — CRITERE sans les lignes à VT mal découpée (30/09, ~12h00 Paris) — C02 rejetée, C02b ADOPTÉE
Constat O23 : les 4 échecs CRITERE de caladr sont des lignes où la VT colle ou coupe des mots ; la mesure compare au nombre de Word de la VT. C02 (exclure si l'adjugée ≠ VT en nombre de mots et la lecture = l'adjugée) exclut aussi 2 lignes de hackherz non confirmées par l'audit → rejetée. C02b (exige en plus l'accord des deux relecteurs de l'audit, `c02/audit_mots.json`) : 23 lignes exclues, toutes vérifiées fautes de VT ; CRITERE 24 → 27/52 (cingdei, ferrepit, brieetli). Audit complémentaire de 5 lignes de caladr (4 confirmées). Régénération de caladr avec T01b : texte 10/3, recherche 0,886 → 0,931. Détail : c02/RESULTATS.md.

## Inventaire des échecs CRITERE restants après C02b (30/09, ~12h10 Paris, CPU)
25 pages en échec : 15 seulement par lignes en échec (8 à une seule ligne), 3 par frontières (≤ 0,5c < 95 %), 1 par pire erreur, 6 cumulent. Lignes en échec (diagech.py) : (a) nombre de mots ≠ VT dans des lectures antérieures à P6d (abréviations collées : « Thren.3. », « Exerc.107.diſt.2. », « vff.xxxviij.jar », « L.S. ») — la consigne actuelle les corrige, les lectures archivées ne sont pas refaites ; (b) fautes de VT que l'adjudication n'a pas retenues (« bitrihuat », « exalio ») ; (c) **11 lignes sans ligne kraken appariée (IoU < 0,5) sur 6 pages** : titres et colophon (durrgeda), entrées de liste courtes (geomeikud « j. Jsop », « ij. Treer »…), titres de section (euanaua « Am I. Sontag »), manchette (herbdulc), incipit à lettrine (extraudeu). (c) est le verrou de segmentation à traiter ensuite.

## S14 — lettrine incluse dans la première ligne et le premier mot (30/09, ~12h55 Paris) — ADOPTÉE
Littérature L24 ; la VT SBB met la lettrine dans la boîte du premier mot (8 lignes / 74 pages, toutes avec la lettre suivante en capitale : « ES », « DA », « AUf », « WJe », « NEgotium »). `lettrine.py` : composante ≥ 1,8 hm, ≤ 8 hm, largeur 0,6-4 hm, hauteur ≤ 3 × largeur, juste à gauche d'une ligne et hors de toute ligne ; appliquée si le mot lu commence par deux capitales ; ligne publiée = union, premier mot = union, autres mots sur la boîte d'origine. Premier passage : 28 filets verticaux pris pour des lettrines → contraintes de forme ajoutées avant mesure. Mesure : euanaua CRITERE 2 → 1 échec, rappel de lignes 0,909 → 0,955 ; extraudeu 4 → 3, txt+IoU80 0,897 → 0,903, rappel 0,810 → 0,857 ; hermhyst, brochrnx (faux positifs écartés par la condition textuelle) identiques ; aucun déclenchement ailleurs. Détail : s14/RESULTATS.md.

## Constat — le placeur de mots tourne sans sa branche CTC (30/09, ~13h10 Paris)
Diagnostic des frontières de BiedBern (9 frontières > 0,5c sur 171 : la coupure tombe dans un petit blanc interne au mot, 4 px, au lieu du vrai blanc voisin de 20-30 px, composition serrée du XIXe s.). En remontant `compose.py` (B20 : CTC d'abord, DTW si le CTC échoue) : le CTC charge `catmus-print-fondue-large.mlmodel` depuis un chemin macOS (`~/Library/Application Support/htrmopo/…`) **absent du conteneur**, et kraken n'est pas installé dans l'environnement de mesure → **toutes nos boîtes de mots viennent du repli DTW**. Sur le banc d'origine (Petit Parisien), CTC 99,65 % ≤ 0,5c / pire 0,66c contre DTW 98,18 % / 1,32c. Récupérer le modèle (Zenodo, DOI 10.5281/zenodo.10592716) est bloqué : zenodo.org et huggingface.co refusés par le proxy (403) ; PyPI et raw.githubusercontent.com passent. À demander au mainteneur : autoriser zenodo.org. En attendant : piste sans nouveau modèle (Tesseract LSTM, boîtes de caractères) pour choisir le blanc de coupure.

## W02 — coupure de mots choisie par Tesseract (30/09, ~14h40 Paris) — ADOPTÉE (critère figé tenu), recul sur le romain
Littérature L25. `w02.py` : pour chaque frontière dont les deux mots sont appariés à des mots Tesseract consécutifs, si notre séparateur n'est pas dans le blanc Tesseract, la coupure passe au milieu de ce blanc, bords recalés sur l'encre. 52 pages : CRITERE 27 → 28 (BiedBern 94,7 → 99,4 % ≤ 0,5c), aucune page perdue ; txt+IoU80 43,947 → 44,025. Critère figé tenu → adoptée. Mais par écriture : Fraktur +0,256 (11 gains, 5 reculs), romain −0,178 (1 gain, 9 reculs ; frontières : 0 gain, 13 reculs). O24 (pages neuves Fraktur, W02b = W02) : somme +0,033, ≤ 0,5c +2,6 pts, mais buchdas (Schwabacher) −0,021 → critère par page de W02b non tenu. Suite : W02c (désactiver sur le romain), à valider sur pages neuves en romain. Détail : w02/RESULTATS.md.

## O24 — 4 pages neuves en Fraktur (30/09, ~14h40 Paris)
Chaîne complète (P6e, T01b, S14, C02b, audit). Texte adjugé audité : AusdeErb 1, backhart 2, buchdas 9, heptaldai 1 (VT distribuée 1/3/18/2) ; CRITERE 2/4 ; recherche médiane 0,982 ; 1 ligne non placée / 113. Audit : 1 verdict annulé sur 9. Détail : o24/RESULTATS.md.

## O25 + W02c — 4 pages neuves en romain (30/09, ~15h15 Paris) — W02c ADOPTÉE
Chaîne complète (P6e, T01b, S14, C02b, audit : 2 verdicts annulés sur 20). Texte adjugé audité : AphoqvSuS 2, AyrmThes 5, BrenBreu 1, culmsent 2 (VT distribuée 14/6/11/4) ; CRITERE 1/4 ; recherche médiane 0,956. W02c (W02 désactivée sur le romain) : txt+IoU80 3,331 sans W02 contre 3,315 avec, ≤ 0,5c 397,75 contre 395,66, CRITERE identique → critère tenu, W02 limitée au Fraktur (`BBVLM_W02C`, défaut 1). Effet indésirable relevé : P6e fait détacher « De » en fin de ligne (AyrmThes), la VT le garde. Détail : o25/RESULTATS.md.

## Inventaire après O24/O25 (30/09, ~15h25 Paris, CPU)
Pages lues en P6e (O23-O25, 12 pages, 369 lignes) : une seule ligne détachée à tort par la règle « deux blocs » (AyrmThes « De ») → pas de changement de consigne. Lignes en échec CRITERE des pages neuves (O24/O25, 6 lignes) : toutes des désaccords de blancs — VT collée (« dẽnachgeenden », « vffkommen », « Oportetid »), lecture collée (« VerboDEI »), tiret (« no— » / « noch — »), « De » détaché. Aucune incohérence interne texte de ligne / éléments Word dans les 82 VT préparées (2 272 lignes). Les blancs restent la frontière commune du texte et des boîtes.

## OLR sur les 12 pages neuves O23-O25 (30/09, ~15h35 Paris, CPU, lecture A, consigne P6e)
Rôle exact par ligne : 1,00 sur 11 pages ; abdipre 0,10 parce que la VT type son texte courant « other » (région temporaire non typée « tempReg… ») — lacune de la VT, pas de la lecture. F1 « même région » : 1,00 sur 9 pages, AyrmThes 0,904 (12 régions VT, 8 lues), abdipre 0,708, culmsent 0,689 (5 régions VT, 3 lues : paragraphes fusionnés). Ordre des régions : ≥ 0,95 sur 10 pages, branchri 0,90, abdipre 0,33 (même cause). L'OLR des pages ordinaires est donc au niveau des mesures O10-O17 (rôles médiane 1,00) ; restes : découpage des paragraphes (culmsent, AyrmThes).

## État consolidé (30/09, ~16h10 Paris)
ALTO des 60 pages régénérés avec la chaîne actuelle (S14, W02/W02c, T01b ; 56 archivés, tous valides XSD). CRITERE (C02b) : 31/60 (O07-O17 23/44, O18 3/4, O23 2/4, O24 2/4, O25 1/4). Lignes : rappel médian 1,000 (50/60 ≥ 0,95). Recherche : médiane 0,962 (38/60 ≥ 0,95). Non placées ≈ 21 / 1 801. Journaux : etat_0930/.

## P01 — seconde lecture sélective par désaccord A/Tesseract (30/09, ~16h30 Paris) — RÉFUTÉE
55 pages : A seule 386 éd., complète 299, sélective (tiers au signal le plus haut) 365 → 24 % du gain gardé (< 80 %). Le signal suit un peu les erreurs de A (ρ = 0,31) mais pas le gain de la seconde lecture (ρ = −0,05). Mesure annexe sur les 12 pages neuves O23-O25 : la seconde lecture + arbitre retire 15 éd. sur 45 (−33 %), jamais pire que A. Détail : p01/RESULTATS.md.

## W02d — W02 sur le romain avec script/Latin (30/09, ~17h10 Paris) — REJETÉE
25 pages en romain : somme txt+IoU80 21,069 (sans W02) contre 21,009 (W02 script/Latin) ; 2 gains, 6 reculs > 0,01. Le modèle d'écriture ne fait pas mieux que le modèle de langue sur l'antiqua ancienne ; W02c reste. Détail : w02d/RESULTATS.md.

## Correction — horodatages (30/09, 11h40 Paris réelles)
Les heures « Paris » écrites dans les entrées et protocoles du 30/09 à partir d'O23 (≈ 08h25) jusqu'à W03 sont fausses : elles avancent de 5 à 6 heures (ex. « ~17h25 » pour W03 = en réalité ≈ 11h25). L'ordre des expériences et les protocoles figés avant mesure restent exacts ; l'heure réelle est celle des commits (UTC+2). Les horodatages suivants sont pris sur l'horloge du conteneur convertie en heure de Paris.

## W03 — coupure de mots par le CTC Calamari (30/09, ≈ 11h50 Paris) — REJETÉE
Calamari 2.3.1 + modèles GT4HistOCR (git, accessibles) installés ; positions votées des caractères pré-calculées sur 60 pages (cala_page.py, ≈ 6 s/page). Règle : déplacer la coupure vers le seul blanc d'encre voisin contenant une espace Calamari. CRITERE : O18 3/4 → 0/4 (mode « tout »), O25 1/4 → 0/4 (mode « romain »), pires erreurs 5-13c. Calamari place des espaces dans les mots (texte lu imparfait sur nos images non binarisées) → coupures déplacées à tort. Détail : w03/RESULTATS.md.

## 2026-09-30 11h53 — W04 : alignement CTC kraken CATMuS (négatif)
O18 : CRITERE 2/4 contre 3/4 par défaut, IoU en baisse sur 3 pages (brieetli 0,971 → 0,926), geomeikud pire 0,16 → 3,18 c. Rejeté. Voir w04/RESULTATS.md.

## 2026-09-30 11h59 — R02 : relecture P6e des trois pages périmées
extraudeu 42 → 2, herrkurt 28 → 20, hermhyst 23 → 24 (chant sous portée : fusion de deux blocs persistante). Total 93 → 46 : hypothèse (≤ 45) manquée de peu, hermhyst empire d'une éd. Les chiffres R02 remplacent les anciens (bilan 58 pages glyphe 304 → 257, norm 260 → 201). Voir r02/RESULTATS.md.

## 2026-09-30 12h30 — W03b adoptée : CRITERE 31 → 32/60
Calamari (GT4HistOCR) sur lignes binarisées Otsu, espaces appariées par rang aux frontières lues seulement si leur nombre est égal ; romain seulement. O07-O17 24/44 (+1), autres lots inchangés ; pire écart en baisse sur 12 pages, aucune page ne franchit 2 c. Première mesure invalide (les scripts de mesure ignoraient le mode romain_b ; corrigé). Voir w03b/RESULTATS.md.

## 2026-09-30 13h03 — M01 : métadonnées depuis la page de titre (premier test mesuré)
VT de métadonnées enfin accessible (MODS SBB via OAI ; images IIIF après 503 intermittents). 12 œuvres tirées, 1 passe Opus : 35/40 champs présents justes (87,5 %, hypothèse ≥ 90 % manquée), 0 année fausse, titre 12/12 ; 2 des 4 faux sont des formes latines gardées par le catalogue, 2 sont des erreurs de rôle ou de nom (traducteur/compositeur, Ferrarius Montanus). Voir m01/RESULTATS.md.

## 2026-09-30 13h18 — M01b : consigne révisée des rôles d'auteur (rejetée)
11 œuvres nouvelles : 33/38 justes (86,8 %), 2 auteurs faux ; M01 sur les mêmes pages : 33/37 (89,2 %), 0 auteur faux. La règle praeses/respondant gagne 1 auteur, l'exemple « Aepinus reste Aepinus » en fait perdre 2 (formes latinisées gardées). Rejetée. Voir m01/RESULTATS_M01b.md.

## 2026-09-30 13h49 — L01 : langue de la consigne (demande de l'utilisateur)
48 lectures Opus (4 pages × 3 langues × 4) : somme des médianes glyphe FR 30,5, EN 36,5, DE 38,5 (norm 17 / 22 / 26). Le français n'est battu sur aucune page ; écart net seulement sur buchdas (Fraktur 1530). On garde la consigne française. Voir l01/RESULTATS.md.

## 2026-09-30 14h12 — V01 : vote par médoïde sans arbitre (négatif)
Sur les lectures L01 : médoïde de 4 FR 28 éd., de 12 lectures 29, contre 17 pour la chaîne actuelle (2 lectures + arbitre) et 30,5 pour une lecture seule. Erreurs corrélées entre lecteurs ; l'arbitre qui revient à l'image fait le gain. Voir v01/RESULTATS.md.

## 2026-09-30 14h19 — V02 : arbitrage élargi par signal Calamari (négatif)
80 lignes signalées sur 12 pages, arbitre Opus : 47 → 60 éd. (caladr 3 → 16 : défaut de construction, codes PUA montrés à l'arbitre) ; hors caladr 44 → 44 ; l'arbitre garde la lecture Opus sur 72/80 lignes. Rejeté. Voir v02/RESULTATS.md.

## 2026-09-30 14h21 — M02 : auteurs mesurés par identité GND
Re-mesure (critère figé avant calcul) : M01 35 → 36/40 (90 %), M01b 33 → 34/38, M01c 33/37 inchangé. Faux restants : rôle, forme vernaculaire absente des autorités, flexion, formes latines du catalogue pour lieu/imprimeur. Voir m01/RESULTATS_M02.md.

## 2026-09-30 14h45 — W05 adoptée : alignement forcé CTC, CRITERE 32 → 33/60
Viterbi CTC du texte lu sur les émissions kraken CATMuS (log des probabilités, correctif du forced_align kraken), frontière entre pics recalée à l'encre. Pire écart médian 1,04 → 0,44 c, pages > 1 c : 31 → 5 ; IoU médiane 0,943 → 0,929. Les échecs restants sont des lignes en échec. Voir w05/RESULTATS.md.

## 2026-09-30 14h58 — R3/R4 : blancs de ponctuation (rejetées au critère, audit à faire)
CRITERE O07-O17 25 → 26/44 (buchdas/24), lignes en échec en baisse, mais texte 96 → 98 à cause d'un verdict d'adjudication ancien (hackherz, forme collée « 2.Cor.XII.3.4 ») ; contre la VT distribuée hackherz 12 → 9. Rejetées au protocole ; audit aveugle du verdict (A02) avant réévaluation. Voir r34/RESULTATS.md.

## 2026-09-30 15h00 — A02 : audit aveugle du verdict hackherz (maintenu)
Deux relecteurs aveugles : « 2. Cor. XII. 3. 4 » (identique à R4), ni la VT ni le verdict ; règle A01 non remplie, verdict maintenu, R3/R4 restent rejetées. Constat : verdicts antérieurs à P6d hétérogènes avec la convention actuelle des blancs. Voir a02/RESULTATS.md.

## 2026-09-30 15h18 — Référence reproductible et R5 adoptée
- Report des lectures R02 dans les lots (extraudeu 3 → 2 lignes en échec, herrkurt 2 → 4). Cache W05 rendu reproductible (même chemin float32 au premier appel) ; référence complète depuis le cache : CRITERE **33/60** confirmé (etat_1515/).
- Cause herrkurt : fractions « 1½ » lues soudées, VT « 1 ½ » (3/0). R5 (blanc entre entier et fraction) : texte herrkurt 20 → 17, lignes en échec 4 → 1, autres pages identiques. Adoptée.

## 2026-09-30 15h25 — A03 : audit C02b de 3 lignes restantes → CRITERE 35/60
Trois lignes où adjugée et lecture s'accordent contre la VT sans audit : les deux relecteurs aveugles confirment le compte de l'adjugée (9/9, 10/10, 6/6 contre VT 7, 9, 5) → exclues par C02b. backhart et culmsent passent ; CRITERE 33 → **35/60**. Voir a03/RESULTATS.md, etat_1525/.

## 30/09 15h40 — A04 / C02c : audit aveugle des lignes à compte de mots ≠ VT
22 lignes, 2 relecteurs aveugles Opus. 7 lignes où les deux relecteurs ont exactement notre compte (≠ VT) → exclues par C02c (règle pré-enregistrée c02c/PROTOCOLE.md, code g01.charge, c02c/audit.json). 13 lignes : relecteurs = VT → erreurs de notre chaîne (4 blancs d'abréviation/parenthèse = forme R3/R4 ; 2 soudures ; 1 fusion de lignes). 2 en désaccord. CRITERE 35 → **39/60** (herrkurt, emmeprac, erasexom, caladr ✓). Voir c02c/RESULTATS.md, etat_c02c/. Suite : A05 (révision des blancs du verdict hackherz l006, pré-enregistrée) puis réévaluation R3/R4.

## 30/09 15h50 — A05 + R3/R4 adoptées
A05 (révision des seuls blancs du verdict hackherz l006, pré-enregistrée, appuyée par A02/A04 et la règle OCR-D niveau 2 « les blancs séparent uniquement des mots », L34). Sous A05, R3/R4 tiennent le critère figé : texte 60 → 54 sans hausse ; CRITERE 39 → **40/60** (buchdas/24 ✓, aucune page en recul). Adoptées par défaut. Voir c02c/RESULTATS.md, etat_a05/.

## 30/09 16h00 — incident d'environnement (Orli) et restauration
Installation d'Orli dans venvk : dépendance kraken~=7.0.2 → kraken 7.1.1 rétrogradé en 7.0.3 et torch 2.14.0 → 2.12.0. Aucune mesure n'a tourné entre-temps. Restauré (kraken 7.1.1, torch 2.14.0, torchvision 0.29.0, orli désinstallé de venvk) ; reproductibilité vérifiée sur le lot O18 contre etat_a05/. Orli isolé dans un venv à part (venvo, torch CPU). Zenodo désormais joignable (poids Orli 594 Mo).

## 30/09 16h50 — S15a Orli (segmenteur de bout en bout) : rejeté
Orli sur les 2 premières pages à ligne manquée : rappel VT 15/22 et 19/26 contre 21/22 et 25/26 pour kraken ; 43 et 90 lignes produites (sur-segmentation) ; aucune ligne manquée récupérée ; ~135 s/page CPU. Rejeté. Constat : « Am I. Sontag » (euanaua) est une ligne de titre coupée en deux par kraken et trop basse (capitales ornées) → piste S15b (union + extension verticale). Voir s15/RESULTATS.md.

## 30/09 17h10 — S17/S17b rejetées ; changement de paradigme
S17b (fusion des boîtes orphelines, contrôle d'encre) : geomeikud/37 3 → 1 mais hackherz 2 → 3 et 852691769 6 → 10 → rejetée. Constat (question de l'utilisatrice : « es-tu sûr d'explorer le bon paradigme ? ») : les règles S02c, S08, S09, S09c, S11, S12, S14, S17 sont des cas particuliers d'un même problème (quelle région d'image explique chaque ligne lue ?), chacune réglée sur 1-2 pages des 60 qui servent aussi à juger → rendement ≈ 1 page par règle et risque de sur-ajustement. Nouveau plan :
1. jeu tenu à l'écart (O23-O25, 12 pages) : plus aucun développement dessus ; CRITERE rapporté séparément dev / écart ;
2. segmentation par reconnaissance guidée par le texte connu (SR) : candidates larges (lignes kraken, fusions/scissions de voisines d'une même bande, extensions à l'encre, bandes de projection), score = vraisemblance de l'alignement forcé CTC (W05) de la ligne lue sur chaque candidate, affectation globale sans chevauchement ; une seule règle, sans seuil par page ;
3. même outil pour le texte : vraisemblance CTC pour départager les désaccords des deux passes Opus (soudures « ihmviel », « VerboDEI »).

## 30/09 17h35 — SR (segmentation par reconnaissance) adoptée
Candidates = lignes de la chaîne + unions de morceaux voisins d'une même bande ; score = perte CTC W05 de la ligne lue ; choix glouton global sans recouvrement ; seules les unions choisies remplacent leurs morceaux. v1 (hongrois) et v2 perdaient des lignes (défauts d'algorithme, scores justes) ; v3 : aucun recul sur dev (48 pages) ni écart (12 pages), geomeikud 3 → 1 ligne en échec, gains de précision sur 3 pages ; CRITERE 40/60 inchangé. Adoptée. Suite : D (VLM arbitre de candidates numérotées, message GPT), scissions SR, affinage GPU si jeton Kaggle/Modal.

## 30/09 17h50 — SR : scissions adoptées ; extensions + marge δ en mesure
Scissions v3 (bandes d'encre neutre et sombre) : durrgeda 3 → 2, aucun recul, adoptées. Extensions à l'encre + marge δ = 0,5 (une candidate nouvelle doit battre nettement la ligne d'origine) : lignes à numéro de liste retrouvées sur geomeikud/34 et /37 ; mesure complète en cours. Voir s15/RESULTATS.md.

## 30/09 18h25 — T03 (tirets de fin de ligne par planches de vignettes, L37) : négatif
Erreurs de texte restantes souvent systématiques par page (eberbrev 13/14 = « ⸗ »/« - »). Planches de vignettes des 412 fins de ligne coupées (51 pages), décision simple/double par relecteurs Opus sans notre lecture. T03 (1 relecteur) 221 → 208 mais 2 pages en hausse ; T03b (accord de 2) 221 → 210, extraudeu 1 → 3 ; T03c (vignettes agrandies) 221 → 223. Décisions instables selon l'instrument, convention VT irrégulière : piste close. Voir t03/PROTOCOLE.md.

## 30/09 18h40 — T04 (ů → uͤ par lexique hunspell) : négatif ; bilan des erreurs de texte
Types d'erreurs restantes (58 pages, 216 signes appariés) : ů/uͤ 26, blancs 22, tirets simples/doubles 17, points 11, ſ/s 8, ß/ſ 6 (DasWeL)… Les deux premières classes « systématiques » (tirets T03, ů/uͤ T04) suivent des conventions de la VT qui varient d'un livre à l'autre : herrleyc écrit « uͤ » pour l'anneau d'inflexion, herbdulc garde « ů » ; les décisions visuelles (T03) sont instables. Ces classes relèvent surtout du bruit de convention de la référence ; le reste est dispersé (≤ 3 signes par type). Voir t04/PROTOCOLE.md.

## 30/09 18h50 — SR extensions à l'encre adoptées ; CRITERE 41/60 (dev 34/48, écart 7/12)
Extensions (prolongement à l'encre dans la bande, arrêt aux colonnes pleines) + marge δ = 0,5 : dev 32 → 34/48 sans recul ; écart 8 → 7/12 (AusdeErb 0 → 1, non diagnostiquée). Adoptées au critère dev ; premier recul observé sur le jeu tenu à l'écart, rapporté tel quel.

## 30/09 19h05 — M03 : métadonnées, lieu et imprimeur par identité (97,4 %)
Re-mesure pré-enregistrée : lieu par entité GND (lobid, variantes latines), radicaux latins pour lieu et imprimeur. M01 38/39 (97,4 %), M01b 37/38, M01c 35/37. Faux restants = interprétation du rôle (dalarie) et autorités dédoublées (goskeinf). Changement de mesure, pas gain de lecture. Voir m01/RESULTATS_M03.md.

## 30/09 19h20 — M04 (colophon, 6 dernières images) : négatif, instrument défaillant
Images = gardes, plats, mires ; seul ferrepit montre un colophon par transparence (1509 juste ; « Wirtzburgij » probablement mal lu pour Wittenberg ; « Viridimontanus » = Grünenberg traduit, non reconnu par la règle de radical). 1 juste, 2 faux sur 11. M04b : pages choisies par la structure METS (bloc « colophon », exclusion des plats/gardes/mire).

## 30/09 19h35 — M04b (colophon par la structure METS) : 6 justes, 2 faux, 3 absents — non tenu de peu
Le bloc logique « colophon » du METS SBB désigne la bonne page (AmmoLIBR, ferrepit, herrleyc) ; buchdas n'a pas de colophon. Colophons lus : Frankfurt 1578 (héritiers Egenolph), Wittenberg 1509 (Viridimontanus = Rhau-Grunenberg), Schmalkalden 1589 (Michel Schmück). Les 2 « faux » sont des formes de nom de la même personne (variantes GND) : une règle d'identité imprimeur serait post hoc, non appliquée ; à valider ailleurs.

## 30/09 19h55 — M05 : métadonnées validées sur 12 œuvres neuves — 95,6 %, 0 année fausse
Œuvres jamais utilisées (1 sur 3 parmi les 43 restantes), page de titre + colophon (structure METS), 1 passe Opus, mesure M03 + identité GND auteur/imprimeur : 43/45 champs présents justes, 0 année fausse (hypothèse ≥ 90 % tenue). Faux : interprétation (Emerico à Rosbach → Rosbach), page de titre française d'un catalogue bilingue. Voir m01/RESULTATS_M05.md.

## 30/09 20h05 — T05 (soudures détectées par les blancs d'encre intra-mot, L40) : négatif
Alignement W05 + largeur du blanc à chaque frontière de caractère : blancs inter-mots de 0 à 17 px, intra-mots jusqu'à 7 px, recouvrement complet dans ces imprimés serrés ; les soudures connues (« ihm|viel », « rbo|DEI ») ne ressortent pas. Close. Voir t05/RESULTATS.md.

## 30/09 20h15 — T06 (vérification des espaces, lecture montrée) : négatif — ancrage sur le candidat
Sur les 22 lignes A04 : 1/12 soudures corrigées, 1/7 lignes justes cassées. Le même modèle, en aveugle, retrouvait la bonne segmentation (A04). Les relectures de contrôle doivent rester aveugles. Voir t06/RESULTATS.md.

## 30/09 20h35 — T07 (espaces d'une relecture aveugle ligne à ligne) : pilote
T07 brut 51 → 100 (report des blancs mal aligné autour de la ponctuation) ; T07b (blancs entre lettres seulement) 41 → 40 (un glissement) ; T07c (+ confirmation par le contexte local dans les deux lectures) : hackherz 4 → 2 (« ihm viel », « Glaͤubige tragen », « diß Leben »), aucune autre page touchée. Critère tenu sur le pilote, gain faible, variantes ajustées sur le pilote → validation sur d'autres pages dev nécessaire avant adoption. Voir t07/RESULTATS.md.

## 30/09 21h00 — T07c validation (7 pages dev) : nulle ; non adoptée
Aucune modification retenue par le garde-fou sur 210 lignes (les accords des relecteurs portent sur les blancs de la ponctuation et sur des glissements d'alignement). T07c ne corrige que hackherz (qui passe alors CRITERE) : coût 2 passes VLM/page pour 1 page sur 11 → non adoptée ; procédure sûre, gardée en réserve pour un mode de correction ciblée.

## 30/09 21h05 — SR consolidée : lignes 51/60, recherche 45/60, CRITERE 41/60
Gain minimal 5 nats + pas de candidate nouvelle pour une ligne d'un mot : lignes ≥ 0,95 50 → 51 (contre 47 avec SR brut), recherche ≥ 0,95 38 → 45 par rapport aux ALTO du matin ; CRITERE 41/60 (dev 34/48, écart 7/12). ALTO sr3 = référence (page.alto.sr3.xml).

## 30/09 18h45 — SR : extensions des unions (adoptée) ; oracle idée D (close)
- Littérature : L41 Set-of-Mark (marques numérotées, choix d'étiquette par le VLM).
- BBVLM_SR_UNION_ETEND=1 : CRITERE 41 → **42/60** (dev 35/48 : euanaua ✓ ; écart 7/12 inchangé), aucun recul. Adoptée (défaut '1').
- Oracle D avant toute passe VLM (sr.py : export BBVLM_SR_DUMP) : sur 1 646 lignes de référence ≥ 2 mots, 11 sans appariement, dont 2 seulement avec une candidate appariable → plafond ≈ 1 ligne : idée D close sans dépense VLM (résultat négatif utile). Les échecs restants viennent des mots (nombre de mots ≠ VT) et de lignes d'apparat absentes de toutes les candidates.
- ALTO sr4 en cours de régénération, puis mes_alto.

## 30/09 18h55 — T08 : signal Calamari/Tesseract pour cibler la relecture des blancs — négatif
- Nombre de mots lu ≠ Calamari et Tesseract : 20 % des lignes signalées, 42 % des 48 lignes à nombre de mots faux couvertes (précision 6 %) ; Calamari soude aux mêmes endroits que nous. Pas de dépense VLM. Détail : t08/RESULTATS.md.
- Décomposition des 27 lignes en échec CRITERE (42/60) : 18 nombre de mots (soudures/coupures de lecture, erreurs de ligne), 9 lignes sans boîte (apparat, colonnes).

## 30/09 19h00 — R4 réappliquée aux textes finaux (oubli) + A05 goclprop — CRITERE 43/60
- Constat (en cherchant les soudures autour de la ponctuation, L42) : R3/R4/R5 adoptées à 15h50 n'avaient pas été réappliquées aux textes finaux de toutes les pages. outils/r4b.py : 2 lignes seulement changent sur 60 pages (BrenBreu « Thren.3. » → « Thren. 3. » ; goclprop « Exerc.107.diſt.2. » → « Exerc. 107. diſt. 2. »). Sauvegardes *_avantR4b.txt.
- goclprop : le verdict adjugé l000/l009 collait les blancs ; les deux relecteurs aveugles A01 et la VT ont la segmentation en 4 mots, verdict ≠ seulement par les blancs → règle A05 pré-enregistrée appliquée (c02c/a05/blancs.json). Texte adjugé : BrenBreu 1 → 0, goclprop 8 → 8 (11 → 8 sous le verdict révisé).
- CRITERE : BrenBreu ✓ (1 → 0 ligne en échec) ; goclprop 2 lignes en échec (la manchette « Exerc. 107. diſt. 2. » échoue désormais faute de boîte, plus au compte de mots ; « eſtque deductio » = lecture juste, VT « eue deduio » sans signe). **43/60** (dev 36/48, écart 7/12). etat_r4b/.

## 30/09 19h20 — S18 (taches détachées aux extrémités des boîtes de ligne) — adoptée
- Littérature L43 (retrait des petites composantes, survey Likforman-Sulem). Motivation : la perte CTC ne pénalise pas le vide en trop, donc SR ne resserre jamais ; post-traitement des boîtes finales.
- CRITERE 60 pages : 43/60 inchangé, lignes en échec 27 → 26 (goclprop manchette retrouvée), aucun recul (écart : AusdeErb iou −0,003, statut inchangé). Adoptée (BBVLM_S18=1). ALTO sr4 relancé avec S18.

## 30/09 19h45 — O26 (4 pages neuves) : SR neutre hors réglage ; une page parfaite
- Protocole pré-enregistré (o26/PROTOCOLE.md, tirage sha256). Chaîne complète : 2 lectures Opus P6e + arbitre, adjudication A2 (2 arbitres aveugles).
- H-O26 tenue : CRITERE 1/4 avec et sans SR/S18, 9 lignes en échec dans les deux cas, boîtes identiques (SR ne choisit que des lignes kraken d'origine sur ces pages). Oracle : 4 lignes sans boîte, aucune candidate ≥ 0,5.
- Texte adjugé : 852691769/512 **0** (53/53), baltdiss 1, culmsent 2, buchdiss 11. Échecs CRITERE de buchdiss = 5 lignes « „ ␣ » → R6 (L44) préparée, non adoptée (inspirée par O26) : à valider sur O27.
- Écarts de mise en œuvre signalés : lectures lancées avant les zooms (refaites), mesures parallèles sur un fichier commun (refaites en série).

## 30/09 20h00 — O27 (R6 sur 4 pages neuves avec « „ ») : H-O27 tenue sans gain → R6 adoptée (preuve faible)
- Tirage amendé avant lecture (seules 2 « dernières pages » avaient « „ »). 8 lectures Opus avec zooms vérifiés, arbitrages, ALTO valides XSD (4/4).
- R6 ne modifie **aucune ligne** sur O27 : les lecteurs y collent déjà « „ » (backhart 20/20, briedefra 7/7). Le seul « „ ␣ » observé reste une lecture de buchdiss (O26). Hypothèse tenue (aucune hausse), sans démonstration de gain → R6 adoptée par défaut (règle OCR-D documentée L44, 0 effet sur 60 pages dev + 8 neuves) ; appliquée à buchdiss (5 lignes).
- Constat annexe : fiscfrie/15 imprime un guillemet de forme « « » (vérifié sur l'image) que la VT normalise en « „ » (12) ; nos lecteurs écrivent « « » : convention de la VT, pas une erreur de lecture (cf. T03/T04).
- En cours : CRITERE O27, adjudication A2 (2 arbitres).
- Incident (20h05) : outils/r4b.py (application de R3/R4/R6 aux textes finaux) prenait toute ligne commençant par « [ » pour un préfixe de rôle ; sur briedefra/131 (lignes imprimées « [Es kann… », « [Dieſe… ») il a dupliqué 2 lignes dans p3i_final (texte 5 → 351 éd.). Corrigé (préfixe de rôle = motif « [rôle] » ou « [rôle+] » seulement), fichier restauré depuis sa sauvegarde ; vérifié : les 3 autres réécritures (BrenBreu, goclprop, buchdiss) ne touchent que les lignes voulues (1, 1, 5). CRITERE O27 relancé (la 1re mesure avait lu le texte corrompu).
- Texte adjugé O27 (A2, 2 arbitres) : backhart/120 **0** (26/26), fiscfrie/15 **0** (22/22), briedefra/131 1, fiscfrie/17 3.

## 30/09 20h20 — ALTO sr4 : recherche ≥ 0,95 45 → 47/60 ; S19 rejetée
- ALTO sr4 (60 pages, chaîne actuelle) : lignes ≥ 0,95 51/60 inchangé ; recherche ≥ 0,95 45 → 47 (euanaua, goclprop, caladr). Seul recul 852691769 (0,875 → 0,863 lignes), attribué aux extensions des unions (ablation).
- S19 (L45 : a priori de largeur par signe pour les candidates nouvelles) : ne corrige pas 852691769 et fait perdre la recherche sur euanaua → rejetée (désactivée).

## 30/09 20h25 — Passes VLM sur pages neuves (O26+O27, 8 pages, sans nouvelle lecture)
- Texte glyphe contre la référence adjugée : lecture A seule 28 éd., lecture B seule 17, chaîne (2 lectures + arbitre + inflexion + R-règles) **11** (−61 % contre A). Par page A → final : 0→0, 1→1, 16→6 (buchdiss), 0→0, 3→0, 4→1, 1→0, 3→3. Aucune page où la chaîne fait pire que A.
- Confirme hors jeu de réglage que la seconde lecture est rentable (dev : −23 %, O23-O25 : −33 %) ; la variance entre lecteurs reste forte (A 28 contre B 17 sur les mêmes pages). Le mode économe (A seule) n'est pas recommandé.

## 30/09 20h30 — Apport des vues zoom (données fortuites O26, 6 lectures sans zoom)
- Contre la référence adjugée (glyphe) : avec zoom 30 éd., sans zoom 26 (baltdiss 1/2 contre 1/1, buchdiss 16/11 contre 7/17, culmsent 0/0 contre 0/0). Aucun gain détectable ; la variance entre lectures (buchdiss 7 à 17) domine.
- Portée : 3 pages, 2 lectures par condition, conditions non tirées au hasard (lectures sans zoom lancées par erreur) → observation, pas un résultat. Les zooms doublent environ le nombre d'images par lecture (coût). Piste Z01 (sobriété) : lecture sans zoom contre avec zoom, ≥ 4 lectures par page et par condition (règle O20), pages à signes suscrits incluses (motif initial des zooms : ä/aͤ/ů).

## 30/09 20h40 — Z01 (zooms utiles ?) : H-Z01 rejetée, zooms gardés
- 24 lectures (3 pages × 2 conditions × 4). Total avec zoom 189 éd., sans zoom 309 (+63 %) ; pire cas buchdas 40 → 68, DasWeL 12 → 25 ; erobdefoa 0/0. Les erreurs sans zoom portent sur les signes suscrits et abréviations des imprimés du XVIe s. Détail : z01/RESULTATS.md.

## 30/09 20h45 — OLR sur 8 pages neuves (O26+O27, lecture A, consigne P6e ; aucune nouvelle lecture)
- Rôle exact : 1,00 sur 7/8 (852691769/512 : 0,962, tableau) ; ordre des régions ≥ 0,90 partout (1,00 sur 6/8) ; F1 « même région » 1,00 sur 5/8, pires 852691769 0,33 (tableau : 25 régions VT, 14 lues), briedefra 0,62 (6 régions VT, 8 lues), culmsent 0,72 (5 VT, 4 lues : listes de sentences).
- Même profil que O23-O25 (rôles 1,00 sur 11/12, F1 1,00 sur 9/12) : rôles et ordre tiennent hors réglage ; le découpage en régions dépend des conventions de la VT pour tableaux et listes.
