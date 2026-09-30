# T03 — forme du tiret de fin de ligne décidée par planche de vignettes (L37), pré-enregistré 30/09 18h05

Constat : parmi les 240 éd. glyphe restantes, des erreurs systématiques par page (eberbrev 13 « ⸗ » VT / « - » lu sur 14). Hypothèse : montrer au VLM toutes les fins de ligne coupées d'une page côte à côte (vignettes localisées par l'ALTO de la chaîne), sans notre lecture, et lui demander simple « - » / double « ⸗ », avec cohérence par poinçon, corrige ces erreurs.
- 51 pages, 412 tirets (outils/t03prep.py) ; 2 relecteurs Opus (moitié des pages chacun, sans candidats).
- Application : le dernier signe de la ligne lue est remplacé par la décision (« ? » : inchangé).
- Critère (figé) : texte glyphe contre l'adjugée (gly.py) sur les 58 pages : total en baisse ET aucune page en hausse ; rapporté aussi pour O23-O25 séparément.

## Résultat T03 (1 relecteur par planche) — REJETÉE
19 signes changés ; texte (51 pages) 221 → 208 : eberbrev 14 → 2, heptaldai 9 → 6, cingdei 13 → 12 ; mais extraudeu 1 → 3 et abdipre 0 → 1 (O23, écart) : critère « aucune page en hausse » non tenu.

## T03b — pré-enregistrée (18h10) : accord de deux relecteurs
Seconde lecture des mêmes planches, lots croisés (le relecteur neuf lit l'autre moitié). Un signe n'est changé que si les deux relecteurs donnent la même forme. Même critère figé.

## Résultat T03b (accord de deux relecteurs, vignettes 90 px) — REJETÉE
Accord 404/412 ; 15 signes changés ; 221 → 210 (eberbrev 14 → 2, cingdei 13 → 12) ; écart O23-O25 27 → 27 ; mais extraudeu 1 → 3 (les deux relecteurs lisent « - » là où VT et lecture ont « ⸗ »). Examen : la vignette (hauteur de ligne ramenée à 90 px) écrase un double trait fin en simple trait (« ican= »). Défaut de l'instrument, pas de la règle.

## T03c — pré-enregistrée (18h20) : vignettes resserrées sur le tiret et agrandies
Vignette = dernier 0,7 h de la ligne + 0,25 h de marge, bande verticale 10-90 % de la ligne, hauteur 200 px (LANCZOS). 4 relecteurs Opus (deux indépendants par lot), changement seulement si les deux concordent. Même critère figé (total en baisse, aucune page en hausse ; écart rapporté).
