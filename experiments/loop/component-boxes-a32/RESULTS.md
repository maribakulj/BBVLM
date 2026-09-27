# A32 — gains CPU et pertes de ponctuation

2026-09-27. Expérience terminée sur les huit pages A28 **déjà consommées**,
261 lignes et 1 753 mots. Aucun nouveau VLM ni nouvel OCR. Les lignes, le texte
et les tokens restent oracle; les alignements CTC proviennent d'A28 et les
baselines sont synthétiques. Ce n'est pas une comparaison de systèmes complets.

| Méthode | IoU moyenne | Rappel IoU ≥ 0,50 | Rappel IoU ≥ 0,80 |
|---|---:|---:|---:|
| PERO natif, protocole A28 | 0,58259 | 68,91 % | 11,07 % |
| CTC + Otsu brut A28 | 0,83882 | 93,44 % | 68,45 % |
| Filtre de surface | 0,84681 | 94,12 % | 70,51 % |
| Composantes du corps seules | 0,87535 | 97,32 % | 77,64 % |
| Corps + satellites | **0,89379** | **97,72 %** | **81,75 %** |

Corps + satellites améliore 385 mots, en dégrade 15 et laisse 1 353 inchangés
par rapport à Otsu. Six régressions dépassent 0,10 d'IoU. Les moyennes et le
rappel IoU80 progressent sur chacune des huit pages, mais la page 00000274
n'atteint que 66,79 % de rappel IoU80. Les composantes du corps seules donnent
403 régressions : rejeter cette ablation comme solution sûre.

Coût supplémentaire mesuré : 0,727 s environ pour la variante avec satellites,
contre 0,621 s pour surface et 0,586 s pour corps. Évaluateur complet 2,60 s.
Les prérequis historiques A28 étaient 36,336 s de reconnaissance et 2,552 s
d'alignement : ils ne deviennent pas gratuits parce qu'ils sont en cache.
La voie minimale souhaitée reste texte VLM + alignement nécessaire + géométrie
CPU; cette expérience ne prouve pas encore sa qualité avec texte/lignes prédits.

## Inspection effective des pixels

Le parent a inspecté `extremes.jpg` (12 pires régressions et 12 meilleurs gains)
puis `regressions-clean.png` (original sans marques / Otsu / pixels retenus).
Les meilleurs gains éliminent bien de l'encre de lignes voisines. Les trois
premières régressions ont une cause visuellement claire :

- `P00000274_l727`, token 2, `M***.` : point final perdu, IoU 1 → 0,661.
- `P00000019_l10`, token 9, `fertile,` : virgule perdue, 0,974 → 0,765.
- `P00000274_l1928`, token 0, `1725.` : point final perdu, 1 → 0,863.

Pour `démon-`, `vée`, `été`, l'accent principal reste visible; des très petits
fragments supérieurs disparaissent. Leur appartenance à l'accent ou au bruit
reste à arbitrer. Ne pas les déclarer automatiquement erreurs de référence,
ni affirmer que tous les accents ont été préservés. La référence originale
est conservée, le dénominateur n'est pas modifié.

## Décision et suite

Conserver corps + satellites comme candidat de développement; **ne pas le
promouvoir dans la production**. Les scores restent conditionnels aux entrées
oracle et aucune porte de validation finale n'est franchie. La prochaine
hypothèse utile est l'attachement des petits signes guidé par le texte déjà
reconnu, afin de distinguer ponctuation attendue et bruit sans nouvelle passe
VLM systématique. Il faut mesurer aussi les faux rattachements, protéger les
signes non reconnus et figer ensuite une validation réellement indépendante.

Le premier calcul de proximité utilisait les rectangles des composantes.
Un test synthétique a révélé un faux rattachement : remplacé par une dilation
des pixels avant consultation des scores réels. Le premier calcul avait déjà
fini; code, empreinte et sorties sont conservés dans `initial/`. La correction
ne change aucun seuil. Deux tests synthétiques passent : accent/hampe/bruit
éloigné et conservation des tokens sur cellule vide ou ponctuation seule.

Reproduction : `PYTHONPATH=src:scripts .venv/bin/python scripts/evaluate_component_boxes_a32.py`
puis `scripts/audit_component_boxes_a32.py`, avec le même interpréteur et PYTHONPATH.
Les originaux TIFF/XML et le cache des boîtes A28 ont des empreintes identiques
avant/après. Les identifiants, textes et nombres de tokens sont invariants.
