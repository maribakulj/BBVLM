# État de la boucle BBVLM

Mis à jour à chaque itération. Lire ceci d'abord.

## Objectif (demande du mainteneur, 2026-09-28)

Vérité terrain patrimoniale « comme si un humain était derrière », avec le
minimum de passes VLM : texte à 0 %, ALTO parfait, segmentation parfaite, OLR,
métadonnées, retrieval ; système fiable, automatisable, reproductible, sobre.

| étage | cible | mesure gelée | état |
|---|---|---|---|
| texte | 0 faute par page | `outils/cer.py` (diplo), référence adjugée règle A2 | pages neuves O09-O12 (16) : **5 à 0**, 4 à 1 car. ; pires : mise en page (extraudeu, ligne double), latin juridique (emmeprac 9) |
| lignes | toutes trouvées, serrées | `outils/segeval.py` | kraken + G03 : bon sur livres ; page en regard écartée par l'alignement ; réclames parfois manquées |
| boîtes de mots | CRITERE.md puis 100 % | judge / `outils/eval_alto.py` | CRITERE ✓ sur 6 pages dont **erobdefoa parfaite de bout en bout** (texte 0, ≤0,5c 100 %) ; blocage : lignes en échec (nombre de mots) ; lignes inclinées (heptaldai 0,34) |
| ALTO | XSD + provenance + refus | `outils/vers_alto.py` | valide XSD 4.4 ; blocs typés, ReadingOrder (XY-cut S03), lignes non placées marquées |
| OLR | rôles + régions + ordre | `outils/olr.py` | rôles 0,74-1,0, F1 régions ≥ 0,91, ordre ≥ 0,95 (livres) ; presse bloquée (Finlam sur HF) |
| retrieval | rappel/précision avec boîte | `outils/recherche.py` | 88-100 % sur la plupart des pages |
| métadonnées | valeurs citant la source | à définir | pas de VT accessible (MODS vides, catalogues bloqués) |

## Chaîne actuelle (P3 + ALTO)

1. Vues : page réduite + bandes pleine résolution + moitiés ×1,6 (`prep_sbb.py`, `vues_zoom.py`).
2. Deux passes Opus, consigne `outils/consigne_P6.md` (OCR-D niveau 2, écriture déclarée, rôle par ligne, fractions, jetons {florin}/{groschen}).
3. `p2.py` : jetons → PUA, conformité OCR-D des espaces, R1 si Fraktur, R2 (ů/uͤ par lexique).
4. `p3.py` : lignes en désaccord recadrées via kraken, arbitrées par Opus (`consigne_arbitre_P3.md`, repli sur les bandes).
5. I01 : signe d'inflexion de l'imprimeur décidé par page (même appel que l'arbitre P3).
6. `segmente.py` (kraken blla) → `serre.py` (G03) → coupe S02 si manchettes → placement par ancrage Tesseract S05 (repli : XY-cut S03 + chasse S04) → routeur G02 → `vers_alto.py`.
Point d'entrée : `chaine.py prepare | arbitrage | final`.

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

- CRITERE : lignes en échec (nombre de mots lus ≠ référence) — premier
  blocage restant ; diagnostiquer (blancs imprimés, mots coupés, ponctuation
  isolée).
- O13 : valider I01 et la chaîne complète sur pages neuves ; P7 rejetée,
  règle L08 (ligne double) encore à traiter autrement.
- Boîtes : lignes inclinées (B01 sous seuil, à re-mesurer).
- Texte : latin juridique (ſ/s, abréviations), coquilles de l'imprimé.
- Métadonnées : extraction depuis la transcription, valeurs citant leur source.

## Contraintes d'environnement

arxiv, HAL, Gallica, Zenodo, HuggingFace bloqués ; GitHub et PyPI accessibles ;
WebSearch (résumés). kraken 7.1.1 installé (modèle blla livré) ; PERO indisponible.
