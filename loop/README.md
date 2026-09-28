# Boucle BBVLM — vérité terrain patrimoniale au mot

État, règles et prochaines étapes : `ETAT.md`. Journal : `JOURNAL.md`.
Littérature : `LITTERATURE.md`. Veille concurrente (astra) : `CONCURRENT.md`.

## La chaîne, en une ligne par étage

| étage | outil | appel VLM |
|---|---|---|
| vues | `outils/vues_zoom.py` (page, bandes, moitiés ×1,6) | — |
| lignes | `outils/segmente.py` (kraken blla), `serre.py` (resserrement), `coupe.py` (manchettes) | — |
| texte + rôles | consigne `outils/consigne_P5.md`, deux lectures | **2 passes** |
| normalisation | `outils/p2.py` : `ocrd2.py` (espaces OCR-D), R1 (Fraktur), `r2.py` (ů/uͤ) | — |
| arbitrage | `outils/p3.py` : seules les lignes en désaccord | **1 petite passe** |
| alignement | `outils/aligne.py` (lecture → lignes, manchettes par rôle) | — |
| mots | `connexe` (master) + filtre A32 routé (astra A37) — `g02.py` | — |
| ALTO | `outils/vers_alto.py` : ALTO 4.4, blocs typés, ReadingOrder, XSD | — |
| recherche | `outils/recherche.py` : vue diplomatique + vue de recherche, boîtes | — |

Point d'entrée : `outils/chaine.py prepare|arbitrage|final DOSSIER`.

## Mesures (outils séparés, jamais dans la chaîne)

`cer.py` (CER de page, vues strict/diplo/norm), `adjuger.py` + `bilan_adj.py`
(adjudication aveugle X/Y, double arbitre), `olr.py`, `eval_alto.py`,
`critere_final.py` (CRITERE.md), `recherche.py`, `segeval.py`.
