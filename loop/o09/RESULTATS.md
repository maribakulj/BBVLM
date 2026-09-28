# O09 — chaîne complète P5 sur 4 pages neuves (latin, bas-allemand)

| page | texte P3 (diplo, adjugé) | OLR F1 régions / ordre | ALTO : texte exact ET IoU≥0,8 | recherche : rappel / précision |
|---|---|---|---|---|
| AmmoLIBR 110 (latin, romain) | **0,000 %** | 0,91 / 0,90 | 82,4 % | 93,4 % / 100 % |
| baltdiss 24 (latin, romain) | **0,000 %** | 1,00 / 0,93 | 78,6 % | 95,2 % / 96,1 % |
| BrenBreu 69 (latin, romain) | 0,062 % (1 car.) | 1,00 / 0,93 | **92,2 %** | 96,7 % / 97,4 % |
| geomeikud 34 (bas-allemand, Fraktur) | 0,158 % (1 car.) | 0,29 / 1,00 | 78,7 % | 88,0 % / 96,0 % |

- Texte : P3 corrige A (AmmoLIBR 0,708 → 0 ; baltdiss B 0,100 → 0).
- Référence : 6 à 16 caractères faux par page ; abréviation latine « -que »
  codée en zone privée MUFI (U+F50D, U+E8BF) → adjugée q́ꝫ / qꝫ (Unicode standard).
- R2 ne tranche pas le bas-allemand (lexique haut-allemand) ; la référence y
  écrit uͤ, l'arbitre y voit ů : laissé contesté.
- OLR geomeikud : les numéros d'items (« i. Jsop ») sont des titres pour le
  lecteur, du paragraphe pour la référence (convention).
- Boîtes : routeur G02/A37 désormais par défaut (8 pages : égal ou meilleur
  partout, 730277879 IoU80 0,63 → 0,75) ; manchettes placées par rôle
  (herrleyc 0,47 → 0,66).
