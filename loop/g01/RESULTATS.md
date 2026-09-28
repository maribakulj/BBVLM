# G01 — boîtes de mots à partir du texte VLM, noté par CRITERE.md

Texte : lecture primaire (A1/L1) des 9 pages O01-O03, appariée aux lignes de
référence ; boîte de ligne de référence ; boîtes de mots de référence pour
noter seulement. Ligne dont le nombre de mots lus ≠ référence = échec.
(`outils/g01.py`, `scores.json`)

| page | connexe ≤0,5c / pire / IoU méd | connexe+A32 (astra) IoU méd | échecs |
|---|---|---|---|
| borrdisc 18 (romain) | **100 % / 0,00 / 0,937** | 0,955 | 0 |
| borrdisc 19 (romain) | **100 % / 0,00 / 0,929** | 0,956 | 1 |
| actevedef 24 | 98,94 % / **6,41** ✗ / 0,933 | 0,882 | 1 |
| drabnota 389 | 97,89 % / 1,01 / 0,939 | 0,890 | **8** ✗ |
| goskeinf 32 | 97,18 % / 0,79 / 0,940 | 0,946 | 0 |
| betrdrzwt 60 | 94,89 % ✗ / 2,12 / 0,948 | 0,776 | 0 |
| curineux 67 | 96,43 % / 1,36 / 0,919 | 0,940 | 0 |
| ejngerez 20 | 87,92 % ✗ / 2,75 / 0,874 | 0,686 | 0 |
| helfkurt 126 | 96,08 % / 1,42 / 0,950 | 0,770 | 1 |

- `connexe` sur texte VLM : CRITERE entièrement tenu sur 4 pages (borrdisc 18,
  goskeinf, curineux ; borrdisc 19 à une ligne près). Échecs : un pire cas à
  6,4 car. (actevedef), frontières sous 95 % sur deux Fraktur serrés.
- Filtre A32 d'astra greffé sur `connexe` : gagne en romain, **perd nettement
  en Fraktur** (IoU médian 0,95 → 0,77) : il absorbe l'encre des lignes
  voisines — c'est exactement le défaut qu'astra a corrigé en A37 par un
  routeur « sans expansion verticale ». À reprendre avec ce routeur.
- Les lignes en échec viennent du découpage en lignes de la lecture (folio et
  signature groupés sur drabnota), pas du moteur.
