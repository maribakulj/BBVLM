# O10 — résultats (chaîne gelée, 4 œuvres jamais vues)

## Texte (CER diplo contre référence adjugée, règle A2)

| page | P2 A | P2 B | **P3 final** | remarque |
|---|---|---|---|---|
| backhart | 0 | 0 | **0 (0/896)** | 24/24 lignes exactes, sans arbitrage |
| hackherz | 0,06 % (1) | 0,31 % (5) | **0,06 % (1)** | « eſtquod » / « eſt quod » (blanc imprimé ambigu) |
| heptaldai | 0,63 % (7) | 0,81 % (9) | **0,81 % (9)** | ⸗ contre - (arbitres discordants, 3 lignes contestées), « dan̄ » |
| herrkurt | 3,18 % (42) | 2,96 % (39) | **3,03 % (40)** | signes monétaires florin/groschen (PUA SBB) et ½ |

Pire cas : herrkurt. 33 des 40 éditions sont de la notation (signe florin
U+F2E8, groschen U+F2E9, fraction ½) : le texte est bon, la notation absente
de la consigne.

### Développement après O10 (herrkurt consommée — pas une validation)
Consigne P6 = P5 + fractions en un glyphe (½) + signes monétaires par jetons
ASCII `{florin}` `{groschen}` convertis en PUA par p2.py (le lecteur n'émet
pas de PUA brut : 0 sur 2 lectures avec la première version).

| herrkurt | P5 → P3 | P6 1re version (PUA brut) | **P6 jetons** |
|---|---|---|---|
| lecture A | 42 | 32 | **5 (0,38 %)** |
| lecture B | 39 | 27 | **9 (0,68 %)** |

À valider sur pages neuves (O11) avant adoption.

## Boîtes, segmentation, OLR, recherche
- ALTO : 4/4 valides XSD. CRITERE.md : backhart ✓ ; hackherz 5 lignes en échec
  (pire 9,4) ; heptaldai ≤0,5c 78,4 %, IoU méd 0,605 ; herrkurt 84,7 % / 2,84 / 0,816.
- Diagnostic avec lignes de référence : heptaldai IoU méd 0,639 (la
  segmentation est juste : 30/30, IoU ligne 0,962) → **boîtes de mots** : lignes
  inclinées (≈ 40 px de dérive), connexe juge au centre de la boîte et garde
  l'encre des voisines ; une boîte dégénérée (y1 < y0) dans Route. herrkurt
  0,922 avec lignes de référence → erreur de segmentation.
- hackherz : 58 lignes kraken pour 34 — 22 viennent de la page en regard
  (bord du scan) ; l'alignement les écarte (34 TextLine dans l'ALTO). 2 lignes
  non placées, dont la réclame « ſo » que kraken ne détecte pas.
- OLR, recherche : voir JOURNAL (O10).

## Adjudication
Premier arbitre, second avis aveugle sur les lignes partagées. Le second avis
contredit le premier sur la forme du trait d'union (heptaldai l001-l002) →
contestées, référence distribuée gardée. Le premier arbitre avait renversé
ﬂ → ſl sur deux « fl. » (florin) d'herrkurt, contredit par le second : d'où
la **règle A2** (JOURNAL).
