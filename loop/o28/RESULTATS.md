# O28 — résultats (4 pages neuves, chaîne complète du 30/09 21h50)

| page | car. | texte glyphe VT distribuée | texte adjugé (A2+A01) | adjugé norm | lignes exactes | CRITERE | lignes en échec | iou_med |
|---|---|---|---|---|---|---|---|---|
| actevedef/27 (Fraktur, 68 l.) | 5661 | 42 | 17 | 17 | 58/68 | ✗ | 9 | 0,750 ✗ |
| albedm/34 (Fraktur) | 1253 | 3 | **0** | 0 | 33/33 | ✓ | 0 | 0,909 |
| durrgeda/51 (Fraktur) | 1201 | 1 | 1 | 1 | 19/20 | ✗ | 0 | 0,762 ✗ |
| eberbrev/146 (romain latin) | 1017 | 18 | 11 | 3 | 17/25 | ✗ | 1 | 0,949 |

Pire page : actevedef (17 éd., 9 lignes en échec, iou 0,750). CRITERE 1/4.

## Audit A01 (règle 4, obligatoire)
42 verdicts relus à l'aveugle par 2 Opus : 20 confirmés, 22 indécis, **0 annulé** → la référence adjugée tient.
Indécis : surtout un relecteur qui écrit « ü » pour « uͤ » (10) et la convention I/J Fraktur : VT « Ihr/Ihn/Iſt »,
les 2 relecteurs + l'arbitre « Jhr/Jhn/Jſt » (même glyphe imprimé ; convention de la VT, pas une erreur de lecture).

## Analyse des erreurs résiduelles (adjugé)
- actevedef : **8 éd. = blanc après Ergänzungsstrich** (« Luͤge⸗und », VT « Luͤge⸗ und » ; 13/13 dans la VT) → règle R9
  (L49, Duden) ; 4 éd. I/J (VT) ; 2 lettres (te/re, t/c) ; 1 point ajouté ; 1 bruit « (o) » (3 éd.).
- eberbrev : 5 éd. « ⸗ » (VT) contre « - » lu en fin de ligne latine ; 2 « est » (VT) contre « eſt » lu ; aſterior/aſperior.
- durrgeda : 1 éd. (Auserwehlten/Außerwehlten).
- Boîtes : iou_med < 0,8 sur 2 pages Fraktur denses (actevedef, durrgeda) — même défaut que backhart (O27).

## Cumul hors réglage O26+O27+O28 (12 pages)
Texte adjugé : 4 pages parfaites / 12 ; CRITERE 2/12 ; défaut dominant = blancs autour de signes (⸗ und, *), 's, « * * * »)
puis iou_med des boîtes Fraktur denses.
