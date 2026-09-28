# S01 / E01 / G03 — segmentation kraken et premier bout-en-bout ALTO

kraken 7.1.1 (`blla` livré avec le paquet, CPU, ~100 s/page). Lignes prédites
appariées aux lignes de référence (IoU ≥ 0,5). E01 : boîtes connexe à partir
des lignes **prédites** et du texte **lu par le VLM** — aucune donnée de
référence en entrée. G03 : boîte de ligne resserrée sur l'encre contenue dans
le polygone kraken (et non son rectangle). Noté par CRITERE.md (judge).

| page | lignes trouvées | IoU lignes brut → serré | E01 ≤0,5c / pire / IoU méd (serré) |
|---|---|---|---|
| borrdisc 18 | 25/25 | 0,740 → 0,957 | **100 % / 0,00 / 0,930** ✓ |
| borrdisc 19 | 26/26 | 0,742 → 0,954 | **100 % / 0,00 / 0,931** (1 échec de compte) |
| buchdiss 10 | 20/20 | 0,740 → 0,981 | **100 % / 0,43 / 0,945** ✓ |
| drabnota 389 | 18/18 | 0,808 → 0,878 | 98,95 % / 0,58 / 0,937 (8 échecs de compte) |
| curineux 67 | 20/20 | 0,724 → 0,972 | 97,32 % / 1,36 / 0,919 ✓ |
| colechri 12 | 25/25 | → 0,976 | 96,90 % / 1,97 / 0,917 ✓ |
| goskeinf 32 | 31/32 | 0,800 → 0,847 | 95,95 % / 1,93 / 0,933 (1 échec) |
| betrdrzwt 60 | 26/28 | 0,763 → 0,806 | 92,73 % ✗ / 3,25 ✗ / 0,800 |
| actevedef 24 | 59/61 | 0,683 → 0,754 | 90,40 % ✗ / 6,25 ✗ / 0,839 |
| angezelug 86 | 28/29 | 0,707 → 0,794 | 91,15 % ✗ / 1,80 / 0,842 |
| ejngerez 20 | 29/29 | 0,828 → 0,907 | 85,51 % ✗ / 2,54 / 0,819 |
| helfkurt 126 | 31/31 | 0,787 → 0,883 | 88,24 % ✗ / 3,04 ✗ / 0,863 |
| herrtreiw 135 | 15/16 | → 0,861 | 69,44 % ✗ / 5,74 ✗ / 0,578 |

- **Premier ALTO bout-en-bout conforme au critère gelé** sur 4 pages (borrdisc
  18, buchdiss, curineux, colechri), sans aucune référence en entrée.
- Le resserrement G03 améliore toutes les pages (développement sur pages
  déjà vues en géométrie ; à valider sur O06).
- Échecs : Fraktur serrés (frontières), et lignes dont le nombre de mots lus
  diffère de la référence (drabnota : folio/signature groupés par le lecteur).
