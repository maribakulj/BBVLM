# O07 — P3 : deux passes, arbitrage des seuls désaccords — validée

CER diplo contre la référence doublement adjugée (arbitres distincts de celui de P3).

| page | P2-A | P2-B | lignes arbitrées | **P3** |
|---|---|---|---|---|
| 730277879 / 190 (Fraktur) | 2,059 % | 0,000 % | 9/19 | **0,000 %** |
| albedm 31 (Fraktur) | 0,000 % | 0,000 % | 0/34 | **0,000 %** |
| berirev 49 (Fraktur) | 0,000 % | 0,350 % | 2/48 | **0,000 %** |
| AphoqvSuS 20 (latin + grec) | 0,799 % | 1,198 % | 1/32 | 0,799 % |

- P3 ≤ min(A, B) sur les 4 pages ; 3 pages à 0 faute. L'arbitre a su choisir
  B (juste) contre A (e suscrits lus trémas) sur 9 lignes de 730277879.
- Reste : une ligne grecque où les deux passes écrivent π/θ pour les variantes
  imprimées ϖ (et ϑ selon la référence) — les deux passes se trompent pareil,
  l'arbitrage des désaccords ne peut pas le voir. Verdict « partage » d'un seul
  arbitre : contesté, référence gardée.
- Coût : 2 passes page + 12 lignes arbitrées sur 133.

## ALTO de bout en bout (`outils/vers_alto.py`, `outils/eval_alto.py`)

Texte P3 + lignes kraken resserrées + alignement + connexe → ALTO 4.4,
**valide au XSD** (hors ligne) sur les 4 pages ; lignes non placées marquées
`NON_PLACE`, jamais comblées. Noté au mot contre la référence PAGE :

| page | mots placés | rappel IoU≥0,5 | IoU≥0,8 | IoU méd | texte exact ET IoU≥0,8 |
|---|---|---|---|---|---|
| albedm | 186/186 | 100 % | 91,9 % | 0,920 | **91,9 %** |
| berirev | 235/244 | 90,2 % | 81,2 % | 0,954 | 79,1 % |
| AphoqvSuS | 112/118 | 91,5 % | 82,2 % | 0,971 | 79,7 % |
| 730277879 | 142/142 | 84,5 % | 63,4 % | 0,869 | 61,3 % |

Pour comparaison, astra A37 (lignes PERO + A32 routé, texte PERO) : rappel
IoU80 68,6 % sur 4 pages SBB. Ici, avec le texte à 0 faute, 63 à 92 %.

## Audit sans candidats (règle ajoutée après l'alerte d'astra)

Un second Opus relit à l'aveugle, **sans aucune proposition**, les 30
recadrages de lignes arbitrées des deux pages à 0 % (17 lignes distinctes),
lectures passées par la même chaîne déterministe (R1 selon la page).

| page | lignes auditées | concordantes | **contestées** | nature |
|---|---|---|---|---|
| 730277879 | 10 | 8 | 2 | å / aͤ ; l / i ; ſ / f (« opſern ») |
| berirev | 7 | 5 | 2 | ſs / ß ; ꝛ / r ; t / c |

Lecture honnête : 730277879 et berirev sont à **0 faute contre la référence
adjugée, avec 2 lignes contestées chacune** sur des formes de glyphes à la
limite de résolution du scan (quelques pixels). Ce résidu n'est tranchable
que par un œil humain ou une image de meilleure résolution ; il est déclaré,
pas effacé.
