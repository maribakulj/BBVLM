# État de la boucle BBVLM

Mis à jour à chaque itération. Lire ceci d'abord.

## Objectif (demande du mainteneur, 2026-09-28)

Vérité terrain patrimoniale « comme si un humain était derrière », avec le
minimum de passes VLM (idéalement une) :

| étage | cible | mesure gelée |
|---|---|---|
| texte | CER 0 % par page | `outils/cer.py`, vues strict / diplo / norm, par page, jamais en moyenne |
| boîtes ALTO | parfaites | `CRITERE.md` par corpus (frontières ≤0,5 car ≥95 %, pire ≤3 car, IoU médian ≥0,80, 0 ligne en échec, pas de régression vs proportionnel) — seuil à durcir vers 100 % une fois atteint |
| segmentation | parfaite | à définir (lignes : appariement IoU, couverture d'encre) |
| OLR, métadonnées, retrieval | à définir | à définir avant toute expérience de l'étage |

Ordre imposé : OCR texte brut parfait sur une page → ALTO → le reste.

## Règles

0. **Concurrence avec astra** (branche `origin/codex/autonomous-research-a34`) :
   à chaque itération, `git fetch` puis lire ses nouveaux commits et en tirer
   ce qui sert (idées, données, résultats négatifs), consigné dans
   `CONCURRENT.md`. Réveil de la boucle ≤ 2 min ; travailler en parallèle
   des sous-agents en cours.

1. Revue de littérature AVANT toute hypothèse (`LITTERATURE.md`). Réutiliser
   ce qui existe ; ne réinventer que ce qui manque.
2. Lecteurs VLM = sous-agents Claude (Opus, Sonnet) lisant les images, à
   l'aveugle : jamais la référence dans leur contexte.
3. Protocole écrit avant la lecture des résultats ; une page qui a servi à
   régler quelque chose est « consommée » et ne valide plus rien.
4. Résultats négatifs consignés comme les positifs (`JOURNAL.md`).
5. Pas de machine à gaz : un étage n'entre dans la chaîne que s'il bat, mesuré,
   la chaîne sans lui.

## Acquis hérités (master et branche astra)

- `connexe` et A32 (astra) passent `CRITERE.md` sur les pages SBB A28 avec
  lignes et texte de référence ; A32 aussi sur A34, `connexe` y échoue sur un
  ouvrage (pire cas 4,9 car). Voir l'analyse de la branche astra.
- Opus a lu 9/9 lignes Fraktur exactes (master, itération 19) — 9 lignes seulement.
- astra : gpt-6-luna/sol à 0,54–1,73 % sur BnF (pas des modèles Claude).

## Contraintes d'environnement

- Réseau : arxiv, HAL, Gallica, Zenodo, HuggingFace bloqués ; GitHub et
  raw.githubusercontent accessibles ; WebSearch fonctionne (résumés seuls).

## Étape en cours

O01 — OCR texte brut pleine page, SBB borrdisc_689809840 p. 00000018
(27 lignes, français 1770 environ, vérité OCR-D).
