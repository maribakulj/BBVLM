# État de la boucle BBVLM

Mis à jour à chaque itération. Lire ceci d'abord.

## Objectif (demande du mainteneur, 2026-09-28)

Vérité terrain patrimoniale « comme si un humain était derrière », avec le
minimum de passes VLM : texte à 0 %, ALTO parfait, segmentation parfaite, OLR,
métadonnées, retrieval ; système fiable, automatisable, reproductible, sobre.

| étage | cible | mesure gelée | état |
|---|---|---|---|
| texte | 0 faute par page | `outils/cer.py` vue **glyphe** (mêmes signes quel que soit le codage, N01 ; diplo rapporté aussi), référence adjugée règle A2 | **58 pages (O07-O25, R02 le 30/09)** : **257 éd. glyphe** contre l’adjugée auditée, 201 en vue norm ; pages à 0 : 11 (glyphe), 12 (norm) ; médiane norm 2 ; pires : buchdas 37 (dont 24 sur lignes A3 = erreurs de VT), hermhyst/149 24 (chant sous portée), herrkurt 20 (conventions fraction/blanc, VT « � ») ; R02 : extraudeu 42 → 2 par relecture P6e — historique : 46 pages adjugées (O07-O18), vue glyphe : **11 à 0**, 20 ≤ 1, 27 ≤ 2, médiane 2 éd./page ; CER global 0,48 % (267/55 474) ; O18 (pages neuves) : 0, 1, 2, 4 ; O23 (pages neuves, P6e) : 0, 1, 3, 3 (après T01 et audit de caladr) ; total 50 pages (O07-O23) : **281 éd. contre l'adjugée entièrement auditée** (A01 + A01b + T01 : 19 verdicts annulés sur 194), 499 contre la VT distribuée ; pages à 0 : 11/50, ≤ 1 : 20, ≤ 2 : 25/50, médiane 2 ; pire extraudeu 42 ; pires : extraudeu 43, buchdas 37, herrkurt 28, hermhyst 23 ; restes : conventions non homogènes de la VT (blancs, ⸗/-, ü/uͤ), ambiguïtés réelles (ſ/f, J/I, ß/ſſ), structure de lignes rare (lignes côte à côte) |
| lignes | toutes trouvées, serrées | `outils/segeval.py` (TextLine de l'ALTO contre VT) | 60 pages (O07-O25, ALTO régénérés) : rappel médian **1,000** (50 ≥ 0,95) ; pires hermhyst 0,78 (chanson), durrgeda 0,82 (titre), extraudeu 0,86 ; ≈ 21 lignes lues non placées sur 1 801 |
| boîtes de mots | CRITERE.md puis 100 % | judge / `outils/eval_alto.py` | **CRITERE ✓ 33/60** (W05 alignement forcé CTC adoptée le 30/09 : pire écart médian 1,04 → 0,44 c, pages > 1 c 31 → 5 ; échecs restants = lignes en échec) — W03b 32/60 — avant : 31/60 (S14, W02/W02c, C02b ; O07-O17 23/44, O18 3/4, O23 2/4, O24 2/4, O25 1/4) ; échecs restants surtout des désaccords de blancs (VT ou lecture) et des lignes courtes absentes de kraken ; placeur de mots sans CTC (zenodo.org bloqué) |
| ALTO | XSD + provenance + refus | `outils/vers_alto.py` | valide XSD 4.4 ; blocs typés, ReadingOrder (XY-cut S03), lignes non placées marquées ; 17 lignes lues non placées sur 1 498 (O07-O18) dont ≈ 9 refus volontaires de S12 (faux placements évités) ; 44 ALTO archivés régénérés (chaîne S11 + S12), valides XSD |
| OLR | rôles + régions + ordre | `outils/olr.py` | pages neuves O23-O25 (12, P6e) : rôle 1,00 sur 11 (abdipre : VT non typée « other »), F1 régions 1,00 sur 9, ordre ≥ 0,95 sur 10 ; consigne P6 (O10-O17, 32 pages) : rôles médiane 1,00 (29/32 ≥ 0,9), F1 régions 0,998 (25/32), ordre 1,00 (28/32) ; pires : durrgeda (titre), 852691769 (tableau), hermhyst (chanson) ; presse bloquée |
| retrieval | rappel/précision avec boîte | `outils/recherche.py` | 60 pages (O07-O25) : rappel médian 0,962, 38 ≥ 0,95 ; pires hermhyst 0,61 (chanson), 852691769 0,79 (tableau), durrgeda 0,85 (titre) |
| métadonnées | valeurs citant la source | à définir | **M02 (30/09, auteurs par identité GND)** : 36/40 champs présents justes sur M01 (90 %) ; **M01 (30/09)** : VT MODS SBB accessible (OAI) ; 12 pages de titre, 1 passe Opus : 35/40 champs présents justes (87,5 %), 0 année fausse, titre 12/12 ; faux = rôle (traducteur/compositeur), partie du nom, formes latines du catalogue ; lieu/imprimeur souvent au colophon |

## Chaîne actuelle (P3 + ALTO)

1. Vues : page réduite + bandes pleine résolution + moitiés ×1,6 (`prep_sbb.py`, `vues_zoom.py`).
2. Deux passes Opus, consigne `outils/consigne_P6e.md` (P6 + abréviations O21b + deux blocs sur une ligne = deux lignes O22) (OCR-D niveau 2, écriture déclarée, rôle par ligne, fractions, jetons {florin}/{groschen}).
3. P3b : les lignes portées par une seule lecture sont aussi arbitrées. `p2.py` : jetons → PUA, qꝫ → U+E8BF (L1), q́ final → U+F50D (T01b), ’ → ' (L2), conformité OCR-D des espaces, R1 si Fraktur, R2 (ů/uͤ par lexique).
4. `p3.py` : lignes en désaccord recadrées via kraken, arbitrées par Opus (`consigne_arbitre_P3.md`, repli sur les bandes).
5. I01 : signe d'inflexion de l'imprimeur décidé par page (même appel que l'arbitre P3).
6. `segmente.py` (kraken blla) → `serre.py` (G03) → scission S08 (ligne kraken portant deux lignes lues) → renvois chiffrés détachés (S08c) → fusion guidée par le texte (S11) → lignes courtes complétées par l'encre (S09) → lettrine rattachée à sa ligne (S14) → coupe S02 si manchettes (S02c sans rôles, validée par relecture) → placement par ancrage Tesseract S05 (repli par largeur borné par S12 : jamais sur une boîte 3× trop étroite) → boîtes : routeur G02 (DTW ; coupure entre mots choisie par Tesseract quand ses mots s'alignent, pages Fraktur seulement, W02/W02c), redressé par la ligne de base kraken sur les pages penchées (B04 ; bas des mots sur bande pleine, H01) ; boîte de ligne G04b (sans encre voisine) publiée, et utilisée pour les mots sur les pages contaminées (G05) → `vers_alto.py`.
Point d'entrée : `chaine.py prepare | arbitrage | final`. Mode qualité : 2 lectures + arbitre P3/I01 ; mode économe : 1 lecture + I01 (V04, 42 pages : 300 éd. contre 260 en mode qualité, 8 contre 10 pages à 0, ≈ −50 % d'appels VLM).

## Règles

0. Concurrence avec astra (`origin/codex/autonomous-research-a34`) : à chaque
   itération, `git fetch`, lire ses nouveaux commits, consigner dans `CONCURRENT.md`.
   Réveil ≤ 2 min ; travailler en parallèle des sous-agents.
1. Revue de littérature AVANT toute hypothèse (`LITTERATURE.md`).
2. Lecteurs = sous-agents Claude, à l'aveugle. Référence jamais dans leur contexte.
3. Protocole écrit avant la lecture des résultats ; une page qui a réglé
   quelque chose est consommée.
4. Adjudication aveugle X/Y ; **audit A01 obligatoire** (deux relecteurs aveugles sans candidats sur chaque ligne dont la référence change ; verdict annulé s'ils écrivent tous deux la VT) ; **règle A2** : tout texte retenu autre que la
   référence distribuée (texte neuf ou choix de la lecture) exige deux
   arbitres indépendants concordants ; toute page annoncée à 0 % est auditée
   (relecture aveugle sans candidats des lignes arbitrées). Les 0 % valent
   « 0 faute contre une référence corrigée par des arbitres Opus concordants »,
   pas une vérité humaine.
5. Résultats négatifs consignés (R1 réfutée en romain, consensus ROVER négatif…).

## Prochaines étapes
- Métadonnées (30/09) : M01 87,5 % (12 œuvres), M01b rejetée ; faux restants = conventions de catalogue (formes latines conservées, noms latinisés rendus en vernaculaire, rôles). Prochaine : M02 = mesure par identité (forme lue ∈ variantes GND de l'entité liée par K10plus, L32) + lecture du colophon quand la page de titre ne porte pas lieu/imprimeur/année.

- **W02 adoptée** (coupure entre deux mots choisie par Tesseract, bords gardés à l'encre) : CRITERE 27 → 28/52, txt+IoU80 +0,078 ; mais Fraktur +0,256 / romain −0,178 (9 reculs) → **W02c adoptée (O25, 4 pages neuves en romain : sans W02 mieux partout) : W02 limitée au Fraktur**. Rappel : le placeur tourne sans CTC (zenodo.org bloqué).
- O25 (4 pages neuves en romain) : texte 2/5/1/2 contre l'adjugée auditée, CRITERE 1/4, recherche médiane 0,956 ; P6e détache à tort « De » en fin de ligne (AyrmThes).
- O24 (4 pages neuves Fraktur) : texte 1/2/9/1 contre l'adjugée auditée, CRITERE 2/4, recherche médiane 0,982.
- S14 adoptée (lettrine incluse dans la première ligne et le premier mot, si le mot lu commence par deux capitales) : euanaua rappel de lignes 0,909 → 0,955, extraudeu 0,810 → 0,857, aucun recul.
- C02b adoptée (CRITERE 24 → 27/52, exclusions vérifiées une à une). Recherche caladr 0,886 → 0,931 après régénération T01b.
- A01b fait : toutes les références adjugées des 50 pages sont auditées (4 annulés sur 90). Prochaine : reprendre les pires pages texte (extraudeu 42, buchdas 38, herrkurt 28, hermhyst 23) — causes par catégorie, puis une règle mesurée.

- T01 (adoptée) : vue glyphe q; ≡ qꝫ, p2 « q́ final → U+F50D » (−12 éd. sur 3 pages, aucune perte). Leçon : l'adjudication A2 peut partager le biais des lecteurs (caladr : 7 verdicts « q́ » annulés par audit aveugle) → auditer aussi toute page où VT distribuée et adjugée divergent de plus de 5 éd.

- Passes VLM : 2 lectures Opus + arbitre = 226 éd. / 38 pages (glyphe) contre
  284 pour une lecture (V02) ; confiance déclarée écartée (L15) ; Sonnet en
  second lecteur rejeté (O16-S : 5× plus de lignes à arbitrer). Signal a priori testé (P01, désaccord A/Tesseract) : réfuté (24 % du gain gardé) ; la seconde lecture reste systématique (−23 % d'éd. sur 55 pages, −33 % sur O23-O25).
- Lecture : variance mesurée (O20) : ±2-3 éd./page d'ordinaire, mais dérive bimodale possible sur latin juridique abrégé (emmeprac 8 → 65 éd. si le lecteur colle les abréviations)  ; méthode : toute consigne se juge sur ≥ 4 lectures par page. Adoptées ainsi : P6d (espace après un point d'abréviation : dérive 2/4 → 0/4, emmeprac 36,8 → 10,75, O21b) puis P6e (deux blocs sur une même ligne = deux lignes : extraudeu 41 → 12, O22) — consigne de lecture actuelle : `outils/consigne_P6e.md`.
- Texte : restes = ambiguïtés réelles (uͤ/ü, ſ/f, J/I, ß/ſſ) et conventions
  non homogènes de la VT (blancs, ⸗/-) ; vue glyphe (N01) adoptée.
- Boîtes : CRITERE 21/44 ; causes d’échec mesurées : lignes courtes sans ligne kraken (fusionnées dans une ligne longue, ou vues en fragment : S09 en complète une partie) et nombre de mots lu ≠ VT (28 lignes / 1265 = blancs seuls, moitié conventions diplomatiques de la VT, moitié nos erreurs : S10, blancs vérifiés par l’encre, rejeté : positions de caractères nécessaires) ; restes =
  pages à frontières hors seuil (herrkurt, hackherz, berirev, 730277879) ;
  recaler le calcul des mots sur G04b partout (G05 le fait par page).
- Segmentation : lignes non trouvées (titres d'apparat, texte vertical,
  colonnes de renvois 852691769 : S08c détache la colonne quand kraken l'a collée, gain faible, lignes de renvoi encore non trouvées ailleurs) ; Eynollah accessible, non intégré.
- Métadonnées : VT identifiée (export CSV METS/MODS de la SBB, lab.sbb.berlin),
  hôte refusé par le réseau — à autoriser par le mainteneur.
- Toute adjudication suit `outils/consigne_adjudication.md` (jamais la règle testée).

## Contraintes d'environnement

- **Placeur de mots sans CTC** : `src/boxers/compose.py` retombe toujours sur le DTW (modèle kraken CATMuS-Print absent, chemin macOS). Pour l'activer : autoriser **zenodo.org** dans la politique réseau de l'environnement (DOI 10.5281/zenodo.10592716), puis installer kraken dans venv2.


arxiv, HAL, Gallica, Zenodo, HuggingFace bloqués ; GitHub et PyPI accessibles ;
WebSearch (résumés). kraken 7.1.1 installé (modèle blla livré) ; PERO indisponible.
