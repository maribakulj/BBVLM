# Une lecture utile, un ancrage géométrique payé à la demande

Décision de recherche du 27/09/2026, pas architecture déjà validée.

L'objectif n'est pas « PERO complet puis correction VLM ». Le VLM doit faire
une lecture documentaire commune à plusieurs usages, et la géométrie doit
consommer seulement les étages nécessaires. L'originalité éventuelle est celle
de cette combinaison évaluée et du routage contrôlé, pas celle des projections
de pixels, de CTC, du NER ou du simple ajout d'un VLM. Aucune revendication de
priorité scientifique n'est établie par cette revue ciblée.

## Répartition proposée

| Besoin | Calcul normal | Calcul conditionnel | Preuve nécessaire |
|---|---|---|---|
| Lignes/baselines/rectification | Détecteur PERO seul et cropper CPU | Autre détecteur seulement sur défaut mesuré | Couverture, pertes d'encre, temps |
| Régions/colonnes | Sorties déjà calculées + règles | YOLO si son gain justifie une inférence supplémentaire | Ablation PERO seul / YOLO seul / combinaison |
| Texte diplomatique | Une lecture VLM de contextes régionaux adressés | Sol sur risques explicites, pas sur CER inconnu en production | CER sous convention gelée, omissions et hallucinations |
| Articles/suites/rôles | Même lecture : relations entre ancres, pas une seconde transcription | Relecture des relations incertaines seulement | Référence éditoriale indépendante |
| Entités/date/byline/langue | Même lecture : spans cités dans le texte, assertion typée et provenance | Autorité externe quand utile, sans compléter une absence visible | Exactitude des citations et des valeurs |
| Mots ALTO | Pixels + texte final, voie géométrique avec abstention | Logits CTC PERO sur lignes ambiguës uniquement | IoU et erreurs extrêmes, faux passages du routeur |
| Retrieval | Index diplomatique + vue normalisée distincte + graphe d'articles/entités | Embeddings à comparer au lexical | Requêtes et jugements indépendants, citations |
| METS/MODS/PREMIS | Export CPU du graphe et du journal | Revue des champs sans preuve | Liens, schémas, fixité et vérité séparés |

Le cropper géométrique PERO ne requiert pas son réseau OCR. En revanche,
`force_align` demande des log-probabilités CTC : enlever le décodage du texte
ne supprime **pas** le coût de reconnaissance. Réutiliser un cache accélère un
replay, pas la première page en production.

## Contrat de lecture à tester

Un contexte de région/colonne est accompagné d'ancres aléatoires de lignes et
d'une vue permettant d'identifier la ligne visée. Le modèle rend le texte une
seule fois, puis références d'ancres/spans, liens titre-corps/suite/note,
genres et métadonnées visibles. Le logiciel vérifie les IDs, la couverture,
les citations exactes, les limites des spans et l'absence de cycles avant
projection dans le graphe. Une interprétation n'est jamais une métadonnée
observée. Les relations éditoriales incertaines restent partielles.

Ne pas demander au VLM des coordonnées fines de 2000 mots ni reproduire le
même texte dans OCR, NER, résumé et métadonnées. Les coordonnées sont dérivées
du pixel et des ancres ; les citations des enrichissements pointent vers le
texte diplomatique immuable. Les résumés/interprétations restent séparés.
Une seule requête peut contenir plusieurs images : rapporter aussi leur nombre,
leurs dimensions, les tokens et les éventuelles reprises, pas seulement « 1 passe ».

## Ablations avant de défendre le coût du VLM

1. PERO natif, régions/lignes/OCR/boîtes, sans VLM.
2. Layout/crop PERO + VLM texte seul + CTC partout : baseline de superposition.
3. Layout/crop PERO + même VLM + géométrie CPU, CTC seulement après abstention.
4. Même budget visuel que 3, mais sortie OCR + relations + spans sourcés en commun.

Comparer sur mêmes pages et même convention : couverture, CER, IoU/p95/worst,
exactitude des articles/relations, extraction des métadonnées, retrieval avec
preuve, temps de relecture humaine, latence et coût réel (tokens/inférences).
Ne retenir 4 que si son utilité supplémentaire compense son surcoût ET sans
régression OCR/géométrie. Les données de tokens/facturation des sous-agents ne
sont pas exposées ici : elles sont inconnues, jamais inventées ou supposées nulles.

## Résultat A19 et limite immédiate

Le prototype `gap_alignment.py` ne charge aucun réseau OCR ni logit. Sur les
quatre ouvrages d'audit SBB, avec lignes et texte de référence : 50/94 lignes
proposées, 294/623 mots, IoU moyenne émise 0,9453, rappel IoU≥0,5 (abstentions
incluses) 0,4575. Temps CPU 0,067 s dans cette exécution. Sur 20 lignes prédites
avec texte VLM A15 : 18 proposées, 0,010 s, sans GT valide pour les mots.

Échec important : un grain d'encre reçoit un token entier ; un groupe de mots
sans espace annotatif peut décaler les affectations. Les pires IoU sont nulles
malgré un écart marqué entre espaces. Ce routeur ne peut donc pas promouvoir
automatiquement ses sorties. Pas de gain économique end-to-end démontré : il
faut mesurer les lots CTC résiduels et le temps de vérification, pas multiplier
naïvement 3,32 s par une fraction de lignes.

Prochaine hypothèse, à sélectionner sur audit uniquement : test de plausibilité
glyphes/encre/token et stabilité à plusieurs binarisations sans modifier le
texte ; rectification géométrique pour les lignes inclinées ; CTC sur toute
ambiguïté. Ensuite geler et ouvrir les quatre ouvrages réservés une seule fois.
