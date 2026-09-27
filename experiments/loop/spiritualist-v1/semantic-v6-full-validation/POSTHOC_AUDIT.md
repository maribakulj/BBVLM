# Audit post-score A11

Le score demeure inchangé. Luna a inclus le jeton Z5 comme `STREAM`/`NOTICE`,
alors que la source marque le bloc `OTHER`, `READING_ORDER=-1` et `SSU_ID`
séparé. Après le score seulement, le texte source a été lu : il s'agit d'une
note éditoriale complète et intelligible sur le télégraphe atlantique, terminée
par « —ED. ». Pour l'indexation et la fidélité documentaire, la conserver comme
contenu recherchable est probablement utile même si elle reste hors du flux
d'articles principal.

Ce conflit montre une convention annotative, pas une raison de corriger la
réponse ou de remplacer la référence. La prochaine politique doit séparer
`readable/retrievable`, `main_reading_stream` et `editorial_genre`; 0010 est
consommée et ne peut servir à sélectionner cette politique.
