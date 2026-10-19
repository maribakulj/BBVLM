# Convention de production v4, avant essais v4

Cette convention concerne les nouvelles requêtes de lecture. Elle ne modifie
ni PROTOCOLE.md v1, ni sa normalisation d'évaluation, ni les anciens essais.
Les références ne sont jamais des entrées de cette étape.

Le lecteur copie les caractères visibles en NFC, les graphies anciennes,
accents, s long, ligatures, casse et ponctuation. Il ne complète aucun mot
coupé. Un petit blanc de composition devant une virgule/point attaché ne
devient pas un espace de mot ; les véritables séparations de mots sont gardées.

Une **marque de césure identifiée visuellement comme coupure de mot** à la fin
de la ligne se transcrit `-` dans le texte d'entraînement. Le lecteur conserve
aussi sa lecture littérale de la marque dans
`linebreak={"raw":caractère_lu,"role":"hyphenation"}`. Le double trait des
imprimés anciens peut être confondu avec un signe égal ; son rôle doit être
établi visuellement et en contexte, jamais par une substitution automatique
de tous les signes égaux. Une égalité ou autre signe garde son caractère et
le rôle `other`. Une ambiguïté non résolue impose `uncertain=true`.

La transcription brute reconstruite est conservée dans `annotations.json`
et `training.jsonl`, à côté du texte utilisé par le CTC. Les positions restent
associées au texte réellement aligné. L'évaluation rapporte le CER strict de
ce texte, le CER conventionnel v1 inchangé, et un diagnostic strict du texte
brut contre la référence. Les différences typographiques restent visibles.

Les essais v4 comparent une nouvelle variante de modèle et d'entrée visuelle.
Un éventuel gain global ne suffira pas à attribuer causalement le gain au
modèle seul ni à certifier la suite réservée.
