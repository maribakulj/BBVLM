# E1 — résultats (accessibilité de la géométrie, transcription imposée), échelle CPU

Qwen3-VL-2B gelé (révision 89644892), caractéristiques fp32 ; sondes entraînées sur 600 blocs train (ordre sha256), choix de couche sur dev, test évalué une fois. Judge BBVLM (CRITERE) dans le repère du crop.

| bras | test : œuvres au CRITERE | ≤ 0,5 c | frontière médiane | p90 | pire | iou_med |
|---|---|---|---|---|---|---|
| G0 — W05+W06 (boîte de ligne VT fournie) | **7/9** | **97,25 %** | 0,00 c | 0,18 c | 3,4 c | **0,898** |
| G1a — 8 têtes de localisation, sans entraînement | 0/9 | 47,9 % | 0,55 c | 2,9 c | 30 c | 0,221 |
| G1 — états couche 14 → boîte | 0/9 | 32,8 % | 1,02 c | 3,4 c | 27 c | 0,303 |
| G2 — G1 + attention croisée sur carte fine | 0/9 | 33,5 % | 1,00 c | 3,4 c | 24 c | 0,316 |

Couche 28 : iou_med dev 0,05 (G1) / 0,07 (G2) — la dernière couche ne porte presque plus de géométrie ; couche 14 : 0,32.
G2 − G1 par œuvre (iou_med) : +0,013 en moyenne, IC95 bootstrap [0,001 ; 0,020] ; ≤ 0,5 c : +0,65 point.

## Décisions (CONTRAT.md, gelées)
- **H1 non tenue** : aucune œuvre de test à iou_med ≥ 0,8 (seuil : ≥ 50 % des œuvres).
- **H2 non tenue** : gain de la carte fine réel mais sous la marge (+0,013 contre +0,02 ; +0,65 contre +2 points).
- **Go/non-go : non-go** à l'échelle CPU — « localisateur conditionnel non compétitif » face à G0 (0/9 contre 7/9). E2 (contrôles de dépendance) sans objet tant que la géométrie n'est pas acquise ; E3-E6 exigent un entraînement conjoint (GPU).

## Ce que montrent les chiffres (pour la suite, avec GPU)
- Le signal existe dans l'attention : G1a, sans entraînement, place la frontière médiane à ½ caractère — mieux que les sondes apprises (1 c), qui régressent des boîtes entières sans voir le voisinage. Une tête de régression sur 600 blocs avec un backbone gelé ne l'exploite pas.
- Pistes, toutes hors échelle CPU : LoRA limitée du décodeur (plan §8 Phase B) ; sonde initialisée par les cartes des têtes de localisation et prédiction de frontières (pas de boîtes) ; données train complètes (1 495 blocs) ; résolution d'entrée plus forte (patch de 16 px = 1-2 caractères).
- Écarts déclarés : bf16 → fp32 (hôte), tour visuelle sdpa, 10 blocs train > 6 000 patches exclus, 600 blocs train seulement ; G0 reçoit la boîte de ligne VT, les sondes non (G0 est donc avantagé, mais l'écart 0,90 / 0,32 dépasse largement cet avantage).
