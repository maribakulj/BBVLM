# Y01 — résultats (zones YOLO DocLayNet → régions OLR)
Détecteur YOLO26-L DocLayNet, CPU ≈ 1,5 s/page ; 56 pages dev avec rôles (4 sans rôles exclues), 12 de validation ; 92 % des lignes tombent dans une zone.

| variante | dev F1=1,00 (base 31/56) | baisses > 0,02 dev | validation F1=1,00 (base 8/12) | baisses val. |
|---|---|---|---|---|
| Y01a (coupures ajoutées, plus petite zone) | 32 | 4 (extraudeu, dalarie, ferrepit, brochrnx) | 7 | 3 |
| Y01b (YOLO seul) | 25 | 13 | 6 | 3 |
| Y01c (Y01a sans zones emboîtées ≥ 90 %, amendement) | **33** | **0** | 7 | 2 (fiscfrie 1,00 → 0,66 ; 852691769 0,33 → 0,28) |

- H-Y01 rejetée (a, b) ; Y01c tenue sur le dev mais **non tenue en validation** (validation non vierge) → non adoptée.
- Gains réels là où la lecture fusionne des blocs (852691769 0,55 → 0,65, AyrmThes 0,90 → 0,99, extraudeu 0,84 → 0,92) ; pertes quand le détecteur, entraîné sur des documents modernes, découpe un poème ou une liste en plusieurs blocs (fiscfrie).
- Conclusion : un YOLO générique n'apporte pas de gain fiable sur les régions ; il faudrait un détecteur entraîné sur imprimés anciens à la granularité VT (affinage sur LADaS/OCR-D hors évaluation, GPU). Y02 (lignes Doc-UFCN comme candidates de SR) reste à tester.
