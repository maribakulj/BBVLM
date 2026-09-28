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
