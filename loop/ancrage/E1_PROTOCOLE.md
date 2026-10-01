# E1 — accessibilité de la géométrie (transcription correcte imposée) — protocole figé le 01/10 avant extraction

Référence : CONTRAT.md v1. Échelle CPU (écart déclaré au plan : Phase A seule, backbone gelé).

## Extraction (une passe teacher-forcée par bloc, Qwen3-VL-2B révision 89644892, fp32, attention « eager »)
- Image = crop complété en blanc (multiple de 32, ≥ 65 536 px) : transformation crop → entrée = identité (E0).
- Requête d'un mot = position du token qui contient son dernier caractère (E0 : 2,7 % des mots finissent dans un token « ponctuation + \n »).
- États : sorties des couches 14 et 28 du décodeur à la position de requête (deux variantes de couche, plan §8 Phase A).
- Carte fine : sorties du dernier bloc visuel avant fusion (patch 16 px), projetées par une **ACP figée à 256 dimensions** apprise sur les caractéristiques de debug64 (train) — écart déclaré : réduction non apprise imposée par le disque.
- G1a (L55) : têtes choisies sur debug64 (train) = les 8 (couche, tête) dont l'attention de la position de requête vers les tokens image fusionnés (cellules 32 px) a la plus grande masse moyenne dans la boîte VT du mot ; boîte = cellules ≥ 0,5 × max de la carte moyenne des 8 têtes, composante 4-connexe contenant le max, bornes des cellules.

## Sondes (train → arrêt précoce sur dev → test une fois)
- G1 : MLP (2048 → 256 → 4) sur l'état du mot ; sortie = boîte normalisée par les dimensions du crop ; perte L1 + GIoU ; AdamW 1e-3, ≤ 30 époques, graine 17.
- G2 : requête = projection 256 de l'état ; attention croisée dense à une tête sur la carte fine (256 + positions 2D sinusoïdales) ; [requête ; vecteur attendu] → MLP → boîte ; mêmes réglages. Variantes couche 14 / 28 ; choix de la couche sur dev.
- G0 : W05 + W06 (chaîne actuelle) sur la boîte de ligne VT et le texte VT du bloc, dans le repère du crop.

## Mesure
- Judge BBVLM (CRITERE.md) dans le repère du crop, par œuvre de test : ≤ 0,5 c, pire, iou_med, lignes en échec ; plus IoU médiane, p95/p99 des erreurs de frontière, coût (s/bloc).
- Décisions : celles de CONTRAT.md (H1, H2, go/non-go contre G0). Rapport aussi des œuvres de test lues par la boucle.

## Amendement 1 (01/10, avant toute extraction E1)
- Incident : E0 (fp32, 13 Go RSS) tué par manque de mémoire quand l'entraînement S2 a démarré (16 Go au total). E0 arrêté à 23 blocs en fp32 (17 + 6), tous conformes.
- Le CPU dispose d'AMX/AVX512-BF16 → **extraction E1 en bf16** (RSS ≈ 6-7 Go, permet le travail parallèle) ; écart bf16/fp32 des logits et des états mesuré sur 4 blocs de debug64 et rapporté avec E0. Rien d'autre ne change.
