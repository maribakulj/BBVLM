# A25 — audit postérieur

Le protocole et la sélection ont été hachés avant téléchargement, mais le
script d'évaluation ne l'était pas. Les sources ont été ouvertes avant que
l'interprétation exécutable de l'Otsu soit scellée. L'implémentation
`d8f7b8c231684b7d2a4dd0f705834e9bc50ffbc70a46f5be6d416fdaae3dcb0b`
reconstruit littéralement la règle décrite : `IMREAD_GRAYSCALE`, un seul seuil
`THRESH_BINARY_INV|THRESH_OTSU` sur le rectangle source de la ligne, cellules
semi-ouvertes séparées par le milieu arrondi des boîtes CTC, enveloppe de tous
les pixels non nuls, puis repli CTC si la cellule est vide. Ce n'est pas une
reproduction bit à bit démontrée du diagnostic A23.

Le second défaut révélé après ouverture est sémantique : l'ouvrage
`briedefra_788606417` est majoritairement en allemand historique, malgré le nom
qui avait motivé sa sélection. A25 n'est donc pas une validation française. Les
originaux restent inchangés et les résultats sont conservés comme diagnostic
géométrique externe à risque d'implémentation.

Sur 4 pages, 140 lignes et 1 097 mots, PERO natif atteint 84,32 % de rappel
IoU≥0,5 et 16,77 % à IoU≥0,8. Le CTC forcé obtient 84,41 % et 17,14 %. Le
candidat `ctc_raw_otsu_v1` couvre les 1 097 mots, atteint 99,45 % à IoU≥0,5,
84,41 % à IoU≥0,8 et 0,9113 d'IoU moyen. Le test local agrégé passe, mais ne
ferme aucun gate : lignes, texte et ordre des tokens sont oracle ; toutes les
pages appartiennent au même ouvrage ; la GT n'est pas adjudiquée ; il subsiste
six mots sous IoU 0,5 et 171 sous IoU 0,8.

La prochaine validation doit figer protocole **et script** avant ouverture,
échantillonner plusieurs ouvrages déclarés français à partir d'une métadonnée
fiable, publier les résultats par page, et n'autoriser aucune régression par
page. Un lot de presse française avec boîtes de mots et adjudication humaine
reste nécessaire pour la cible finale.
