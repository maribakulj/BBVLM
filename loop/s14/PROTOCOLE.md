# S14 — lettrine incluse dans la première ligne et le premier mot

Figé le 2026-09-30 (~12h25 Paris) avant mesure.
Constat : 8 lignes de VT (74 pages) portent une lettrine dans la boîte du premier mot ; nos lignes commencent après elle (euanaua « ES war », extraudeu « DA der » : IoU 0,28 et 0,21).
Règle : composante connexe de hauteur ≥ 1,8 × hauteur médiane des lignes, ≤ 8 × ; largeur ≤ 4 × ; son bord droit à moins de 1,5 hm à gauche du début d'une ligne (ou jusqu'à 0,5 hm dedans) ; recouvrement vertical avec cette ligne ; hors de toute autre boîte de ligne ; affectée à la ligne la plus haute qu'elle recouvre ; la ligne lue correspondante commence par une majuscule. Effet : boîte de ligne publiée = union(ligne, lettrine) ; premier mot = union(premier mot, lettrine) ; les autres mots calculés sur la boîte d'origine.
Mesure : CRITERE (C02b), eval_alto txt+IoU80, segeval sur les pages à lettrine (betrdrzwt, baroegvi, euanaua, extraudeu, 688357687, dalarie si mesurées) et témoin sur toutes les pages (aucun déclenchement hors lettrines attendu).
Critère : adoptée si aucune page ne recule (CRITERE, txt+IoU80, rappel de lignes) et si au moins une ligne à lettrine passe l'IoU 0,5 ; tout déclenchement sur une page sans lettrine est vérifié à l'image.

## Ajustement avant mesure (30/09 ~12h40 Paris)
Premier passage de la détection seule sur les 52 pages : 33 déclenchements dont 28 filets verticaux (tableaux, bordures) → forme exigée : largeur ≥ 0,6 hm, hauteur ≤ 3 × largeur. Restent 5 : euanaua et extraudeu (vraies lettrines), 2 notes de musique (hermhyst), un grand S Fraktur (brochrnx). Condition textuelle remplacée par « le mot lu commence par deux capitales » (usage typographique : la lettre qui suit la lettrine est en capitale ; vrai pour les 8 lettrines de la VT), ce qui écarte les 3 faux positifs.
