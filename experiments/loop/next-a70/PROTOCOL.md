# A70 — attribution des échecs profonds A69 (diagnostic consommé)

Claude a été recontrôlé à `76056c5c1957e0de4232f0aef1f6cbc7f2893402`,
inchangé. Le parent Codex est `e76a6453859b1bd5462d7abe036e62ab48eadea2` et
master reste `60b8ed3082bbc4ae65fb2a9fecc999a6be21a0ec`. Aucun merge.

A69 rejette `ink_crossing` : le défaut dominant n'est pas une coupe de quelques
pixels. A70 ouvre uniquement les mêmes dix XML déjà consommés et réutilise les
prédictions natives scellées. Pour chaque ligne dont la meilleure boîte native
couvre moins de 50 % de l'aire, mesurer : meilleure couverture individuelle,
couverture par l'union de toutes les boîtes texte, nombre de boîtes contributives
et classes contributives.

Catégories gelées avant calcul : `fragmented_recoverable` si l'union couvre au
moins 95 %, `fragmented_partial` entre 50 et 95 %, `miss_or_convention` sous
50 %. Ceci diagnostique si une fusion de régions peut aider ; ce n'est ni une
nouvelle politique, ni une validation, ni une vérité ALTO parfaite. Aucun OCR,
VLM ou nouveau forward détecteur. Les 100 Test restent fermées.

Le code courant DocLayout-YOLO et le writer A69 ont été relus ; aucune nouvelle
publication n'est revendiquée dans ce diagnostic dérivé. Le résumé primaire
DocLayout-YOLO complet reste celui d'A66 dans `PAPER_SUMMARIES.md`.
