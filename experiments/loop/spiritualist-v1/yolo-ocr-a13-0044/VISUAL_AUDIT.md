# A13 — audit ciblé après lecture aveugle, 27/09/2026

Statut : observations de l'agent principal après accès aux scores ; **pas une
adjudication indépendante**, pas une nouvelle GT. Originaux et XML inchangés.
Images réellement vues à résolution native : les trois crops `input/*.png`.

Luna : 8 éditions / 1 049 caractères (0,7626 %). Sol : 7 / 1 049 (0,6673 %).
Sur les trois régions, la différence Luna/Sol est une espace avant `:—`.
Cette convention ne doit pas servir à déclarer une victoire de reconnaissance.

| ID | Différence avec XML | Observation sur l'image |
|---|---|---|
| Rbadb3783 | virgule après `placed` absente du XML | virgule visible, présente chez Luna et Sol |
| Rbadb3783 | espace avant `:—` absente chez Luna | espace visuel variable ; Sol choisit l'espace de la référence |
| Rba25d296 | apostrophe après `Mechanics` absente du XML | signe visible, présent chez les deux lecteurs |
| Rba25d296 | virgule après `Bavaria` absente du XML | virgule visible, présente chez les deux lecteurs |
| Rba25d296 | tiret de fin de ligne `Spiri-` absent du XML | tiret visible, conservé par les deux lecteurs |
| Rc94b31fb | virgule après `effected` absente du XML | virgule visible, présente chez les deux lecteurs |
| Rc94b31fb | espace et tiret long après `adopted` absents du XML | `:—` visible ; l'espace relève aussi de la convention |

Les lecteurs ne montrent pas de différence de mot dans ce diagnostic. Cela
renforce le besoin d'une référence diplomatique auditée ; **cela ne certifie
pas 0 % de CER** sur ces crops et encore moins sur les pages complètes.
Luna et Sol sont tous deux confiants malgré le désaccord avec la référence :
la confiance déclarée seule n'est donc ni une preuve ni un routeur validé.
Le prompt Sol rappelait en plus le traitement possible des petites capitales
et des ambiguïtés de convention ; le reste du contrat et les images sont les
mêmes. Il ne s'agit pas d'un benchmark pur contrôlé de modèles.

Coût : trois crops / une passe Luna, puis trois crops / une passe Sol ; zéro
nouvelle inférence YOLO. Tokens, coût monétaire et durée interne d'inférence
ne sont pas exposés et ne sont pas estimés fictivement. Les petites images
exactes, requêtes et réponses sont conservées pour audit.
