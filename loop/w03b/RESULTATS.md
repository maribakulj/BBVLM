# W03b — résultats

| lot | état (W02c) | W03b romain |
|---|---|---|
| O07-O17 | 23 / 44 | **24 / 44** (canitrac ✗ → ✓) |
| O18 | 3 / 4 | 3 / 4 (Fraktur, inchangé) |
| O23 | 2 / 4 | 2 / 4 |
| O24 | 2 / 4 | 2 / 4 (Fraktur) |
| O25 | 1 / 4 | 1 / 4 |
| **total** | **31 / 60** | **32 / 60** |

- Frontières : 2 354 frontières romaines éligibles (nombre d'espaces Calamari = nombre de frontières lues sur 476 lignes / 577), 427 déplacées (O07-O17) ; O25 : 101 lignes / 108, 55 déplacées.
- Pire écart par page : baisse sur 12 pages (aepidisp 1,13 → 0,26 c, erasexom 1,16 → 0,26, AmmoLIBR 0,76 → 0,43, ferrepit 0,43 → 0,00, BrenBreu/72 0,32 → 0,08…), hausse sur 2 (abdipre 0,14 → 0,82, busmexpo 0,00 → 0,04), aucune page ne franchit 2 c. IoU médiane : −0,001 à −0,005 sur 3 pages.
- Lecture Calamari binarisée : quasi parfaite (« dem Stuhlgange verſpuͤren laßen: bald » contre « den tuhlgange enſatenlaßenbald » en gris) ; CER seul par page médiane 3,6 % (min 0,3, max 42,8 heptaldai), trop faible pour voter à égalité avec les lectures VLM.
- **Adoptée** (critères du protocole tenus : ≥ 32/60, aucun lot en recul, aucun franchissement de 2 c). Défaut `BBVLM_W03=romain_b`.
- Reste à brancher dans chaine.py : le pré-calcul `BBVLM_CALA_BIN=1 cala_page.py` (environnement Calamari séparé) lit les boîtes de ligne de kraken_crit2.json, écrites aujourd'hui par les scripts de mesure ; sans calamari_bin.json, W03b ne fait rien (repli sur l'état antérieur).
