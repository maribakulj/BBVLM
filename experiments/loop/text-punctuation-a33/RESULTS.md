# A33 — le texte seul ne désambiguïse pas la ponctuation

Expérience terminée le 2026-09-27 sur A28, développement déjà consommé : huit
pages, 261 lignes, 1 753 mots. Aucun VLM ni OCR supplémentaire. Le rattachement
des signes finaux modifie 11 mots : 4 améliorations, 7 régressions, 1 742
inchangés. Les signes initiaux+finaux produisent exactement le même résultat :
aucun signe initial ne déclenche une modification.

| Méthode | IoU moyenne | Rappel IoU ≥ 0,50 | Rappel IoU ≥ 0,80 |
|---|---:|---:|---:|
| Otsu brut A28 | 0,838819 | 93,440 % | 68,454 % |
| A32 corps + satellites | **0,893795** | **97,718 %** | **81,746 %** |
| A33 signes finaux | 0,893394 | 97,661 % | 81,689 % |

A33 perd 0,000401 d'IoU moyenne et 0,057 point de rappel IoU80. Temps CPU
additionnel 1,467 s, contre 0,726 s pour construire A32. Rejeter A33 tel quel :
il est à la fois plus lent et légèrement moins bon.

## Inspection exhaustive des 11 modifications

Le parent a inspecté `all-changes-clean.png`, qui montre les pixels originaux
sans contours, puis les coordonnées A32/A33/référence en texte. Quatre signes
sont effectivement récupérés : la virgule de `fertile,`, les points de `Law.`,
`M***.` et `1725.`. Sept rattachements sont nuisibles : `tenai.`, `1719.`,
`C***`, `p.`, `place.`, `I.`, `ibid.`. Plusieurs blobs proviennent visiblement
de la ligne inférieure ou d'un bruit latéral alors que la ponctuation correcte
était déjà incluse dans A32. La présence d'un signe final dans la transcription
ne dit donc pas si sa composante manque à la boîte.

Observation post-score, non validée : les quatre gains ont une aire de 27 à 69
pixels, six des sept pertes de 5 à 15 pixels; la septième est déclenchée par
`*`, inclus trop largement comme ponctuation finale. Un seuil d'aire et
l'exclusion de `*` seraient un réglage évident **sur ces mêmes pages**; aucun
score sélectionné ainsi n'est présenté. Cette règle devra être gelée avant une
nouvelle référence indépendante. Ne pas transformer cette observation en gate.

## Limites et décision

Texte/tokenisation et rectangles de lignes sont oracle; CTC en cache; baseline
synthétique. A33 ne valide ni boîtes sur texte VLM prédit, ni lignes prédites,
ni système complet. L'image et les annotations sources ont les mêmes SHA-256
avant/après; identifiants, textes, nombres de tokens et dénominateurs sont
préservés. Les deux lancements précédant le rapport final sont archivés : un
fixture de test mal placé puis une sérialisation OpenCV interrompue; aucun score
n'a servi à modifier les seuils gelés.

Conclusion : garder A32 comme candidat de développement, rejeter A33. Pour la
suite, figer sur un nouveau corpus la variante conservatrice issue de
l'observation (aire minimale et pas de `*`), ou estimer explicitement si la
ponctuation est déjà couverte à partir des pas CTC. Aucun gate final ne passe.

