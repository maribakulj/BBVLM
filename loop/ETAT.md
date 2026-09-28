# État de la boucle BBVLM

Mis à jour à chaque itération. Lire ceci d'abord.

## Objectif (demande du mainteneur, 2026-09-28)

Vérité terrain patrimoniale « comme si un humain était derrière », avec le
minimum de passes VLM : texte à 0 %, ALTO parfait, segmentation parfaite, OLR,
métadonnées, retrieval ; système fiable, automatisable, reproductible, sobre.

| étage | cible | mesure gelée | état |
|---|---|---|---|
| texte | 0 faute par page | `outils/cer.py` (diplo), référence adjugée règle A2 | pages neuves O09-O11 (12) : **4 à 0**, 4 à ≤ 1 car. / ≤ 6 car., pires : notation (herrkurt, réglée par P6) et mise en page (extraudeu, ligne double) |
| lignes | toutes trouvées, serrées | `outils/segeval.py` | kraken + G03 : bon sur livres ; page en regard écartée par l'alignement ; réclames parfois manquées |
| boîtes de mots | CRITERE.md puis 100 % | judge / `outils/eval_alto.py` | CRITERE ✓ sur 5 pages ; texte+IoU80 64-93 % sauf lignes inclinées (heptaldai 0,34) et tableaux (852691769 0,14) |
| ALTO | XSD + provenance + refus | `outils/vers_alto.py` | valide XSD 4.4 ; blocs typés, ReadingOrder (XY-cut S03), lignes non placées marquées |
| OLR | rôles + régions + ordre | `outils/olr.py` | rôles 0,74-1,0, F1 régions ≥ 0,91, ordre ≥ 0,95 (livres) ; presse bloquée (Finlam sur HF) |
| retrieval | rappel/précision avec boîte | `outils/recherche.py` | 88-100 % sur la plupart des pages |
| métadonnées | valeurs citant la source | à définir | pas de VT accessible (MODS vides, catalogues bloqués) |

## Chaîne actuelle (P3 + ALTO)

1. Vues : page réduite + bandes pleine résolution + moitiés ×1,6 (`prep_sbb.py`, `vues_zoom.py`).
2. Deux passes Opus, consigne `outils/consigne_P6.md` (OCR-D niveau 2, écriture déclarée, rôle par ligne, fractions, jetons {florin}/{groschen}).
3. `p2.py` : jetons → PUA, conformité OCR-D des espaces, R1 si Fraktur, R2 (ů/uͤ par lexique).
4. `p3.py` : lignes en désaccord recadrées via kraken, arbitrées par Opus (`consigne_arbitre_P3.md`, repli sur les bandes).
5. `segmente.py` (kraken blla) → `serre.py` (G03) → coupe S02 si manchettes → `aligne.py` (XY-cut S03, chasse ∝ corps S04) → routeur G02 → `vers_alto.py`.
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

- O12 (pages neuves) : valider S03/S04, P7 candidate (ligne visuelle à deux
  régions → deux lignes, L08).
- Boîtes : lignes inclinées (B01 sous seuil 0,25 h, à re-mesurer) ; page-
  tableau 852691769 (texte+IoU80 0,14 malgré une segmentation juste :
  diagnostiquer l'alignement ligne par ligne).
- Texte : coquilles et lettres retournées (garder l'imprimé) ; erreurs
  communes aux deux passes.
- Métadonnées : extraction depuis la transcription, valeurs citant leur source.

## Contraintes d'environnement

arxiv, HAL, Gallica, Zenodo, HuggingFace bloqués ; GitHub et PyPI accessibles ;
WebSearch (résumés). kraken 7.1.1 installé (modèle blla livré) ; PERO indisponible.
