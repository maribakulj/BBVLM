# Boucle BBVLM — vérité terrain patrimoniale au mot

État, règles et prochaines étapes : `ETAT.md`. Journal : `JOURNAL.md`.
Littérature : `LITTERATURE.md`. Veille concurrente (astra) : `CONCURRENT.md`.

## La chaîne, en une ligne par étage (état au 2026-09-29)

| étage | outil | appel VLM |
|---|---|---|
| vues | `outils/vues_zoom.py` (page réduite, bandes pleine résolution, moitiés ×1,6) | — |
| lignes | `segmente.py` (kraken blla) → `serre.py` : boîte G03 (encre du polygone) et boîte G04b (sans l'encre des lignes voisines, publiée) | — |
| texte + rôles | deux lectures aveugles, consigne `outils/consigne_P6e.md` (OCR-D niveau 2, jetons monétaires, rôles et régions ; P6 + abréviations O21b + deux blocs = deux lignes O22) | **2 passes** |
| normalisation | `outils/p2.py` : jetons → PUA, qꝫ → U+E8BF (L1), ’ → ' (L2), espaces OCR-D, R1 (Fraktur), R2 (ů/uͤ) | — |
| arbitrage | `outils/p3.py` : seules les lignes en désaccord (et celles d'une seule lecture), recadrées ; même appel : signe d'inflexion de la page (`inflexion.py`, I01) | **1 petite passe** |
| lignes (suite) | `vers_alto.lignes_page()` : scission des lignes portant deux lignes lues (S08, `scinde.py`), renvois chiffrés détachés (S08c, `scinde.renvois`), deux lignes kraken réunies quand une seule ligne lue les porte (S11, `scinde.fusionne`), lignes courtes complétées par l'encre (S09, `etend.py`), manchettes coupées (S02, `coupe.py` ; sans rôles : S02c, coupe gardée si le morceau relu retrouve une ligne lue), boîte G04b pour les mots sur les pages contaminées (G05) | — |
| placement | ancrage par OCR Tesseract des lignes kraken (S05, `ancre.py`) ; repli XY-cut + largeur | — |
| mots | routeur connexe + A32 (`g02.py`) ; pages penchées : redressement par ligne de base (B04) et bas des mots sur bande pleine (H01) (`centre.py`) | — |
| ALTO | `outils/vers_alto.py` : ALTO 4.4, blocs typés, ReadingOrder, lignes non placées marquées, XSD | — |

Mode économe : lecture A seule + I01 (≈ −50 % d'appels VLM, +15 % d'éditions, V04).
Point d'entrée : `outils/chaine.py prepare|arbitrage|final DOSSIER`.

## Mesures (outils séparés, jamais dans la chaîne)

`cer.py` : CER de page, vues strict / diplo / **glyphe** (mêmes signes quel que
soit le codage, `glyphe.py`, N01 — vue de référence) / norm. `adjuger.py` +
`bilan_adj.py` : adjudication aveugle X/Y, deux arbitres (règle A2), consigne
figée `consigne_adjudication.md`. `olr.py`, `eval_alto.py` (texte + IoU 0,8),
`critere_final.py` et CRITERE sur les lignes de l'ALTO (`lignes_page`),
`recherche.py`, `segeval.py`.

Résultats (42 pages adjugées, 44 avec ALTO) : voir `ETAT.md`.

## Installation (reproductibilité)

- Python : numpy, scipy, opencv-python, lxml, wordfreq ; kraken 7.1.1 dans un
  environnement à part (`segmente.py`, modèle blla livré).
- Tesseract 5 (ancrage S05, texte jamais publié) : `apt-get install
  tesseract-ocr`, puis modèles tessdata_best dans `$BBVLM_TESSDATA` :
  `script/Fraktur.traineddata` et `lat.traineddata` depuis
  `https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/`.
  Sans Tesseract, `vers_alto.py` revient à l'alignement par largeur (S04).
- Chaîne : `chaine.py prepare | arbitrage | final DOSSIER` ; lectures et
  arbitrage VLM selon `consigne_P6e.md`, `consigne_arbitre_P3.md`,
  `consigne_inflexion.md`.
