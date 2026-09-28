# A78 — échec du regroupement horizontal sans régions

Une configuration gelée, quatre pages A76 consommées, aucun réglage post-score.

| Page | Groupes fusionnés | Rappel IoU50 avant → après | Références gagnées/perdues |
|---|---:|---:|---:|
|1626|0|100 → 100 %|0/0|
|1785|8|94,51 → 78,02 %|0/15|
|1866|128|85,54 → 47,23 %|0/249|
|1924|69|83,54 → 54,27 %|1/97|

**Rejet : 360 correspondances nettes perdues**, trois pages régressent en précision
et rappel. Les critères sont maintenus. Le cas déterministe `worst-chain.png`,
réellement inspecté, montre quatre lignes de quatre colonnes différentes réunies
par une chaîne de quatre composantes. L'espacement des colonnes est inférieur
à la borne choisie : les hauteurs/centres seuls ne protègent pas la structure.

0,975 s CPU, zéro nouvelle inférence/OCR/VLM/Test. Chaque composante apparaît
une fois dans les sorties et chaque groupe conserve l'enveloppe des entrées.
Cela préserve une surface mais ne préserve pas les unités de lecture.

A79 : tester le rôle de YOLO proposé par l'utilisateur, comme contrainte de
région avant regroupement. Garder la règle A78 inchangée à l'intérieur d'une
région prédite unique, sceller les sorties avant XML ; mesurer le coût réel
et les régressions. Ce sera encore du développement consommé, pas un holdout.
