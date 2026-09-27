# A21 — coût marginal et fausse confiance, 2026-09-27

Défaut observé sur développement A18/A20 : 4 des 6 lignes non signalées comme
incertaines par Luna ont encore des écarts après décomposition documentée.
Hypothèse : uncertainty=false ne permet pas, seul, une sortie certifiée sans
relecture. Ablation : faire lire par un nouveau Sol aveugle les SIX lignes
non escaladées, y compris celles exactes ; pas seulement les lignes erronées.
La décision globale est motivée par les scores déjà consommés, donc pas un
test indépendant. IDs conservés, transcriptions précédentes et GT cachées.

Même isolement polygonal et original de contexte qu'A18. Le prompt rappelle
explicitement les conventions historiques ; modèle, présentation et précision
du prompt changent conjointement face à Luna. Pas d'attribution causale au
seul modèle. Mesurer chaque changement, y compris toute régression.

Source primaire lue : Groot & Valdenegro-Toro, TrustNLP, 21 juin 2024,
https://aclanthology.org/2024.trustnlp-1.13/ et PDF (introduction, expériences
et limites). Ils évaluent la confiance verbalisée sur NLP et scènes visuelles,
avec des modèles plus anciens ; leurs résultats motivent une vérification
empirique ici, sans prouver quoi que ce soit sur notre OCR ou Luna/Sol.
Le code courant du routeur inspecté est prepare_sbb_escalation_a18.py : il
ne retient que bool(uncertain), sans mesure de fiabilité hors échantillon.

Coût : une tâche Sol supplémentaire, six images cibles, contextes effectivement
inspectés journalisés par le lecteur. Tokens et montant facturé inconnus.
Cette ablation achète des lectures pour mesurer le routeur ; elle ne prouve
pas une réduction du coût de production. Originaux et réserve préservés.

## Résultat terminé

Les six cibles et les six contextes ont été effectivement inspectés. Un tour
silencieux prolongé a été interrompu puis repris dans le même agent ; cette
reprise est comptée, coût en tokens/temps de génération non observé.

Sur ces six lignes, CER décomposé : 16/188 → 9/188 (8,51 % → 4,79 %),
trois lignes améliorées, deux dégradées, une inchangée. Une ligne auparavant
exacte est dégradée. Sur les 16 lignes : 45/736 → 38/736 (6,11 % → 5,16 %),
mais exactitude ligne entière 3/16 → 2/16. Strict : 92/707 → 84/707
(13,01 % → 11,88 %). Ce sont des accords à la référence originale, pas des
erreurs adjudiquées indépendamment.

Décision : rejeter le remplacement systématique par Sol et le booléen Luna
comme certificat. Conserver les deux lectures et les conflits, préparer un
routeur fondé aussi sur observations d'image/conventions et une adjudication
indépendante. Ne choisir après coup le meilleur texte par ligne à partir de la
GT : cela ferait une prédiction oracle. Aucun nouveau critère global satisfait.
