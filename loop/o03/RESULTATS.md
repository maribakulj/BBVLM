# O03 — consigne OCR-D, 4 pages Fraktur jamais lues

CER diplo après `ocrd2.py` (qui ajoute désormais l'espace après la virgule
oblique : les deux lectures d'ejngerez la collaient au mot suivant, par
sur-application de ma consigne ; correction déclarée après score sur cette page).

| page | L1 distribuée | **L1 adjugée** | L2 distribuée | **L2 adjugée** | réf. fausse |
|---|---|---|---|---|---|
| betrdrzwt 60 | 0,402 % | 0,402 % | 0,000 % | **0,000 %** | 0 |
| curineux 67 | 0,522 % | **0,000 %** | 1,044 % | 0,522 % | 4 car. |
| ejngerez 20 | 2,378 % | 0,845 % (norm 0,071 %) | — invalide — | | 22 car. |
| helfkurt 126 | 1,840 % | 1,345 % | 0,056 % | 1,065 % ⚠ | 18 car. ⚠ |

- **Deux pages Fraktur jamais vues lues sans faute** par une passe Opus
  (betrdrzwt L2, curineux L1). Avec O01/O02 : 5 pages sur 9 ont au moins une
  lecture à 0,000 % adjugé.
- ⚠ helfkurt : l'arbitre a imposé ů (rond suscrit) sur 9 lignes contre la
  référence ET les deux lecteurs, sans pouvoir agrandir. Verdict « aucun » d'un
  seul arbitre sur un signe suscrit : non fiable. Règle ajoutée pour la suite :
  tout verdict « aucun » exige un second arbitre indépendant concordant.
- ⚠ ejngerez L2 invalide : fichier identique octet pour octet à L1, écrit une
  seconde après (écrasement entre agents). Consigné comme incident.
- Signes suscrits (ü / uͤ / ů / oͤ) = première source de variance entre deux
  lectures d'une même page (helfkurt L1 : trémas partout, 1,84 % ; L2 : e
  suscrits, 0,056 %). C'est une question de résolution des vues.
- Accord L1/L2 comme détecteur : rappel 100 % sur deux pages, 0 % sur les deux
  autres. Inutilisable seul.
