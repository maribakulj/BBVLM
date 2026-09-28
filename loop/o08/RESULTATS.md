# O08 — OLR dans la même passe, et limites de P3

## Texte (P3, référence doublement adjugée)

| page | P2-A | P2-B | P3 | nature des fautes restantes |
|---|---|---|---|---|
| culmsent 25 (latin, romain) | 0,000 % | 0,149 % | 0,075 % | 1 caractère |
| euanaua 143 (Fraktur) | 0,202 % | 0,202 % | 0,202 % | 1 caractère |
| DasWeL 71 (Fraktur XVIe) | 1,818 % | 0,979 % | 1,399 % | ſ pour la ligature ſz (ß), espaces autour des chiffres romains |
| herrleyc 41 (Fraktur XVIe) | 1,815 % | 2,016 % | 1,815 % | ů pour uͤ sur des mots à inflexion (fůr, Sůnde…) |

**P3 n'est pas ≤ min(A, B) partout** (DasWeL) et ne voit pas les erreurs
**communes** aux deux passes (ů/uͤ, ſ/ß). Ces erreurs sont systématiques et
linguistiquement prévisibles → règle R2 (L06) et consigne P5.

## OLR des livres (même passe, 0 appel supplémentaire, `outils/olr.py`)

| page | rôle exact | F1 même région | ordre des régions | régions réf / lues |
|---|---|---|---|---|
| herrleyc | 1,00 | **1,00** | 0,98 | 11 / 11 |
| euanaua | 1,00 | **1,00** | 0,90 | 5 / 5 |
| DasWeL | 0,81 | 0,93 | 1,00 | 11 / 8 |
| culmsent | 1,00 | 0,03 ✗ | 0,96 | 8 / 33 |

culmsent : liste de proverbes ; le lecteur ouvre une région par proverbe, la
référence groupe par bloc visuel → granularité à fixer dans la consigne (P5).
ALTO : TextBlocks typés (LayoutTag du rôle OCR-D) et ReadingOrder, XSD valide.
