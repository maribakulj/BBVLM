# État de la boucle BBVLM

Mis à jour à chaque itération. Lire ceci d'abord.

## Objectif (demande du mainteneur, 2026-09-28)

Vérité terrain patrimoniale « comme si un humain était derrière », avec le
minimum de passes VLM : texte à 0 %, ALTO parfait, segmentation parfaite, OLR,
métadonnées, retrieval ; système fiable, automatisable, reproductible, sobre.

| étage | cible | mesure gelée | état |
|---|---|---|---|
| texte | 0 faute par page | `outils/cer.py` vue **glyphe** (mêmes signes quel que soit le codage, N01 ; diplo rapporté aussi), référence adjugée règle A2 | 42 pages adjugées (O07-O17), vue glyphe : **10 à 0**, 18 ≤ 1, 24 ≤ 2, médiane 2 éd./page ; CER global 0,50 % (260/51 896) ; pires : extraudeu 43, buchdas 37, herrkurt 28, hermhyst 23 ; restes : conventions non homogènes de la VT (blancs, ⸗/-, ü/uͤ), ambiguïtés réelles (ſ/f, J/I, ß/ſſ), structure de lignes rare (lignes côte à côte) |
| lignes | toutes trouvées, serrées | `outils/segeval.py` (TextLine de l'ALTO contre VT) | 44 pages : rappel médian 0,968 (27 ≥ 0,95 ; pire hermhyst 0,78), IoU médian des lignes 0,962 (pire chridiss 0,81), précision médiane 1,00 ; manques : titres d'apparat, texte vertical, colonnes de renvois, lignes côte à côte |
| boîtes de mots | CRITERE.md puis 100 % | judge / `outils/eval_alto.py` | CRITERE ✓ sur 18/44 pages O07-O17 (chaîne actuelle avec S08c + S09, lignes de l’ALTO) ; **erobdefoa, caladr, dalarie, chiamerk (O16, neuve) parfaites de bout en bout** ; blocage : lignes non trouvées par kraken (titres d'apparat, courtes manchettes) et blancs du texte |
| ALTO | XSD + provenance + refus | `outils/vers_alto.py` | valide XSD 4.4 ; blocs typés, ReadingOrder (XY-cut S03), lignes non placées marquées |
| OLR | rôles + régions + ordre | `outils/olr.py` | consigne P6 (O10-O17, 32 pages) : rôles médiane 1,00 (29/32 ≥ 0,9), F1 régions 0,998 (25/32), ordre 1,00 (28/32) ; pires : durrgeda (titre), 852691769 (tableau), hermhyst (chanson) ; presse bloquée |
| retrieval | rappel/précision avec boîte | `outils/recherche.py` | rappel médian 0,956 sur 40 pages, 20 ≥ 0,95 ; pire 0,79 (852691769, tableau à intitulés verticaux ; 0,77 avant S08c) |
| métadonnées | valeurs citant la source | à définir | pas de VT accessible (MODS vides, catalogues bloqués) |

## Chaîne actuelle (P3 + ALTO)

1. Vues : page réduite + bandes pleine résolution + moitiés ×1,6 (`prep_sbb.py`, `vues_zoom.py`).
2. Deux passes Opus, consigne `outils/consigne_P6.md` (OCR-D niveau 2, écriture déclarée, rôle par ligne, fractions, jetons {florin}/{groschen}).
3. P3b : les lignes portées par une seule lecture sont aussi arbitrées. `p2.py` : jetons → PUA, qꝫ → U+E8BF (L1), ’ → ' (L2), conformité OCR-D des espaces, R1 si Fraktur, R2 (ů/uͤ par lexique).
4. `p3.py` : lignes en désaccord recadrées via kraken, arbitrées par Opus (`consigne_arbitre_P3.md`, repli sur les bandes).
5. I01 : signe d'inflexion de l'imprimeur décidé par page (même appel que l'arbitre P3).
6. `segmente.py` (kraken blla) → `serre.py` (G03) → scission S08 (ligne kraken portant deux lignes lues) → renvois chiffrés détachés (S08c) → lignes courtes complétées par l'encre (S09) → coupe S02 si manchettes → placement par ancrage Tesseract S05 (repli : XY-cut S03 + chasse S04) → boîtes : routeur G02, redressé par la ligne de base kraken sur les pages penchées (B04 ; bas des mots sur bande pleine, H01) ; boîte de ligne G04b (sans encre voisine) publiée, et utilisée pour les mots sur les pages contaminées (G05) → `vers_alto.py`.
Point d'entrée : `chaine.py prepare | arbitrage | final`. Mode qualité : 2 lectures + arbitre P3/I01 ; mode économe : 1 lecture + I01 (V04, 42 pages : 300 éd. contre 260 en mode qualité, 8 contre 10 pages à 0, ≈ −50 % d'appels VLM).

## Règles

0. Concurrence avec astra (`origin/codex/autonomous-research-a34`) : à chaque
   itération, `git fetch`, lire ses nouveaux commits, consigner dans `CONCURRENT.md`.
   Réveil ≤ 2 min ; travailler en parallèle des sous-agents.
1. Revue de littérature AVANT toute hypothèse (`LITTERATURE.md`).
2. Lecteurs = sous-agents Claude, à l'aveugle. Référence jamais dans leur contexte.
3. Protocole écrit avant la lecture des résultats ; une page qui a réglé
   quelque chose est consommée.
4. Adjudication aveugle X/Y ; **règle A2** : tout texte retenu autre que la
   référence distribuée (texte neuf ou choix de la lecture) exige deux
   arbitres indépendants concordants ; toute page annoncée à 0 % est auditée
   (relecture aveugle sans candidats des lignes arbitrées). Les 0 % valent
   « 0 faute contre une référence corrigée par des arbitres Opus concordants »,
   pas une vérité humaine.
5. Résultats négatifs consignés (R1 réfutée en romain, consensus ROVER négatif…).

## Prochaines étapes

- Passes VLM : 2 lectures Opus + arbitre = 226 éd. / 38 pages (glyphe) contre
  284 pour une lecture (V02) ; confiance déclarée écartée (L15) ; Sonnet en
  second lecteur rejeté (O16-S : 5× plus de lignes à arbitrer). Piste ouverte :
  signal a priori des pages qui gagnent à la seconde lecture.
- Texte : restes = ambiguïtés réelles (uͤ/ü, ſ/f, J/I, ß/ſſ) et conventions
  non homogènes de la VT (blancs, ⸗/-) ; vue glyphe (N01) adoptée.
- Boîtes : CRITERE 18/44 ; causes d’échec mesurées : lignes courtes sans ligne kraken (fusionnées dans une ligne longue, ou vues en fragment : S09 en complète une partie) et nombre de mots lu ≠ VT (28 lignes / 1265 = blancs seuls, moitié conventions diplomatiques de la VT, moitié nos erreurs : piste S10, blancs vérifiés par l’encre) ; restes =
  pages à frontières hors seuil (herrkurt, hackherz, berirev, 730277879) ;
  recaler le calcul des mots sur G04b partout (G05 le fait par page).
- Segmentation : lignes non trouvées (titres d'apparat, texte vertical,
  colonnes de renvois 852691769 : S08c détache la colonne quand kraken l'a collée, gain faible, lignes de renvoi encore non trouvées ailleurs) ; Eynollah accessible, non intégré.
- Métadonnées : VT identifiée (export CSV METS/MODS de la SBB, lab.sbb.berlin),
  hôte refusé par le réseau — à autoriser par le mainteneur.
- Toute adjudication suit `outils/consigne_adjudication.md` (jamais la règle testée).

## Contraintes d'environnement

arxiv, HAL, Gallica, Zenodo, HuggingFace bloqués ; GitHub et PyPI accessibles ;
WebSearch (résumés). kraken 7.1.1 installé (modèle blla livré) ; PERO indisponible.
