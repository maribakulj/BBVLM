# État de la boucle BBVLM

Mis à jour à chaque itération. Lire ceci d'abord.

## Objectif (demande du mainteneur, 2026-09-28)

Vérité terrain patrimoniale « comme si un humain était derrière », avec le
minimum de passes VLM : texte à 0 %, ALTO parfait, segmentation parfaite, OLR,
métadonnées, retrieval ; système fiable, automatisable, reproductible, sobre.

| étage | cible | mesure gelée | état |
|---|---|---|---|
| texte | 0 faute par page | `outils/cer.py` (diplo), référence doublement adjugée | **P3 : 3 pages sur 4 à 0 % (O07)** ; 15+ pages à 0 % sur au moins une lecture |
| lignes | toutes trouvées, serrées | `outils/segeval.py` | kraken + G03 : 95-100 % trouvées, IoU méd 0,75-0,98 |
| boîtes de mots | CRITERE.md puis 100 % | judge / `outils/eval_alto.py` | CRITERE tenu sur 4 pages bout-en-bout ; IoU80 63-92 % au mot |
| ALTO | XSD + provenance + refus | `outils/vers_alto.py` | valide XSD 4.4 ; lignes non placées marquées |
| OLR, métadonnées, retrieval | à définir | à définir | **pas commencé** |

## Chaîne actuelle (P3 + ALTO)

1. Vues : page réduite + bandes pleine résolution + moitiés ×1,6 (`prep_sbb.py`, `vues_zoom.py`).
2. Deux passes Opus, consigne `outils/consigne_P2.md` (OCR-D niveau 2, déclaration d'écriture).
3. `p2.py` : conformité OCR-D des espaces, R1 (tréma → e suscrit) si Fraktur.
4. `p3.py` : lignes en désaccord recadrées via kraken et arbitrées par Opus.
5. `segmente.py` (kraken blla) → `serre.py` (G03) → `aligne.py` → `vers_alto.py` (connexe).

## Règles

0. Concurrence avec astra (`origin/codex/autonomous-research-a34`) : à chaque
   itération, `git fetch`, lire ses nouveaux commits, consigner dans `CONCURRENT.md`.
   Réveil ≤ 2 min ; travailler en parallèle des sous-agents.
1. Revue de littérature AVANT toute hypothèse (`LITTERATURE.md`).
2. Lecteurs = sous-agents Claude, à l'aveugle. Référence jamais dans leur contexte.
3. Protocole écrit avant la lecture des résultats ; une page qui a réglé
   quelque chose est consommée.
4. Adjudication aveugle X/Y ; une correction qu'aucun candidat ne portait
   exige deux arbitres concordants ; toute page annoncée à 0 % est auditée
   (relecture aveugle sans candidats des lignes arbitrées). Les 0 % valent
   « 0 faute contre une référence corrigée par des arbitres Opus concordants »,
   pas une vérité humaine.
5. Résultats négatifs consignés (R1 réfutée en romain, consensus ROVER négatif…).

## Prochaines étapes

- Texte : valider P3 sur un lot plus large et plus varié (presse, français,
  pages dégradées) ; attaquer les erreurs communes aux deux passes (variantes
  grecques, a priori lexical « Marana ») — un seul arbitre ne les voit pas.
- Boîtes : Fraktur serré (frontières < 95 %), lignes non placées.
- OLR / métadonnées / retrieval : revue de littérature, reprendre l'ordonnanceur
  de colonnes d'astra (A48-A49) plutôt que le réinventer.

## Contraintes d'environnement

arxiv, HAL, Gallica, Zenodo, HuggingFace bloqués ; GitHub et PyPI accessibles ;
WebSearch (résumés). kraken 7.1.1 installé (modèle blla livré) ; PERO indisponible.
