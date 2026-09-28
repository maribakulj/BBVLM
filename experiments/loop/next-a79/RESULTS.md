# A79 — YOLO bloque les jonctions entre colonnes, gain limité

Quatre vraies passes DocLayout-YOLO CPU, après réparation de l'environnement
(détails RUNTIME_RECOVERY.md, premier échec conservé). Sorties finales dans retry/.
Les boîtes et paramètres A78 sont inchangés à l'intérieur d'une région unique.

|Page|Régions texte|Liens autorisés|Composantes sans propriétaire unique|P/R IoU50 après|
|---|---:|---:|---:|---:|
|1626|5|0|9|85,00 /100 %|
|1785|16|0|6|93,48 /94,51 %|
|1866|67|4|121|79,12 /85,69 %|
|1924|45|21|168|61,80 /83,84 %|

Deux références supplémentaires atteignent IoU50 (une en1866, une en1924),
aucune référence n'en sort. Précision/rappel non inférieurs sur chaque page :
le gate local de développement passe. A78 sans régions perdait360 correspondances.
Le gain reste petit et les erreurs absolues restent nombreuses. Les régions
prédisent des blocs, pas un ordre de lecture ni des articles certifiés.

Coût mesuré :8,36s détection,8,93s total du programme (hors imports/préparation),
4 forwards, zéro OCR/VLM/Test. Le coût antérieur des masques Eynollah demeure
payant dans un bilan de système complet ; ne pas le compter gratuit parce qu'il
est en cache. Aucun nouveau package lourd installé, seule NumPy1.26.4 restaurée.

A80 doit tester cette règle inchangée sur quatre nouvelles pages déterministes
non-Test, avec comparaison à la même extraction Eynollah sans YOLO. Exiger
non-infériorité par page et gain positif, sans abaisser les seuils globaux.
A79 reste consommé ; aucun gate scientifique global promu, aucune GT modifiée.
