# C02 — CRITERE : exclure les lignes dont la VT est mal découpée en mots

Figé le 2026-09-30 (~11h20 Paris) avant mesure.
Constat (O23) : les 4 lignes en échec de caladr sont des lignes où la VT colle ou coupe des mots (« Memoresea », « ſcilicetou: », « Vinclapedi », « nu bila ») ; l'adjudication auditée a corrigé le texte, la lecture est juste, mais `g01.charge` compare le nombre de mots lus au nombre de Word de la VT → échec. Les boîtes de mots de la VT ne peuvent pas juger ces lignes.
Règle : une ligne est **exclue** de CRITERE (comptée à part) si le nombre de mots de la référence adjugée auditée ≠ nombre de Word de la VT **et** la lecture a le nombre de mots de la référence adjugée. Toute autre discordance reste un échec.
Mesure : CRITERE (MODE=chaine2) sur O07-O17, O18, O23 avant/après ; lignes exclues par page. Critère : la règle n'exclut que des lignes dont la VT est fautive (vérification de chaque ligne exclue) ; résultat rapporté avec le nombre d'exclues à côté du ✓.
