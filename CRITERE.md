# Critère de réussite — GELÉ le 2026-09-25, avant toute mesure de candidat

Un système est **fiable** quand, sur **CHACUN** des corpus (jamais en moyenne) :

| | seuil |
|---|---|
| frontières à ≤ 0,5 caractère | **≥ 95 %** |
| pire cas | **≤ 3 caractères** |
| IoU médian des boîtes de mots | **≥ 0,80** |
| lignes en échec | **0** |
| régression du pire cas vs proportionnel | **interdite** |

La dernière clause est la leçon de `hans` H1 : le CTC y faisait passer les
frontières mal placées de 16-21 % à moins de 1 % **en moyenne**, et a été
réfuté parce qu'il aggravait le pire cas sur un corpus. Un gain moyen qui
dégrade un corpus n'est pas un gain.

La notation ne regarde jamais une moyenne seule : p90, p99 et pire cas sont
ce qui bouge quand un système est bon sur les lignes faciles et mauvais sur
celles pour lesquelles il existe.

## Ce que le boxer reçoit, et rien d'autre

- l'image en niveaux de gris
- le **texte** de la ligne (mots séparés) — c'est la sortie du VLM
- la **boîte de ligne** — elle viendra d'eynollah/kraken en production

Il ne reçoit JAMAIS les boîtes de mots de la vérité terrain. Celles-ci ne
servent qu'à noter.
