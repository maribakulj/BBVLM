# A31 — Sol sans masque, avec contexte : gain net faible, régressions

Essai réalisé le 27 septembre 2026 à la demande de l'utilisateur. Un nouveau
lecteur gpt-6-sol a inspecté les 32 images (16 cibles + 16 contextes), sans accès
aux anciennes réponses, aux références ni aux lectures du parent.

| Même référence inchangée, 16 régions | Sol A30 masqué | Sol A31 non masqué + contexte |
|---|---:|---:|
| CER normalisé principal | 0,5739 % | 0,5402 % |
| Éditions / 2 962 caractères | 17 | 16 |
| Régions exactes normalisées | 6/16 | 7/16 |
| CER NFC secondaire | 1,4647 % | 1,4314 % |
| Images inspectées | 16 | 32 |

Corrections :

- T009 : `5e` devient `3e` ; le désaccord restant avec `3°` relève de l'exposant.
- T013 : `Mme Faure` devient `Mlle Fabre`, conforme à la référence distribuée.
- T007 : le tiret initial est restauré ; l'apostrophe de `C'est` reste absente
  de la référence, mais est soutenue par l'inspection non aveugle du parent.
- T006 : le point final ajouté disparaît, mais l'espace après le tiret apparaît ;
  le score reste identique malgré une amélioration visuelle probable.

Régressions :

- T010 : `Waché-de Roo` devient `Gaston-Woëché-de Roe` dans le nom complet ;
  le score passe de 1 à 5 éditions. La région est signalée incertaine.
- T011 : `Merey` devient `Mercy`, et `Roumafort` reste inchangé malgré la
  référence `Roumefort` ; 1 à 2 éditions, région signalée incertaine.

`Bouisson` reste inchangé contre `Bouissou` dans la référence (T016, incertain).
Les lectures correctes probables pénalisées par la GT (`judiciaires`, `affaire`,
`Le Sénat`) persistent ; aucune correction de GT n'a été appliquée.

Interprétation : le contexte et la suppression du masque/contour semblent aider
certains caractères, mais une seule passe dans chaque condition ne permet pas
d'isoler l'effet de la préparation de la variabilité du modèle. Le changement
est conjoint : masque, contour, contexte et consigne de délimitation. Le gain
net n'est que d'une édition, et ne démontre pas une méthode fiable à 0 % CER.
Pas de sélection par GT entre A30 et A31, ni de transcription composite.

Coût : une nouvelle tâche Sol, 32 images au lieu de 16 ; 0,61 s d'évaluation CPU.
Les tokens, le temps GPU et la facturation ne sont pas exposés par l'interface.
Les 66 tests logiciels passent (1 fixture omise). Les références et candidats
A30 ont été comparés octet par octet au checkpoint v23 : inchangés.

Suite : politique de relecture des seuls passages incertains à définir sur
développement, sans employer la GT pour choisir la réponse finale ; validation
nouvelle avec règles de normalisation figées et référence adjudiquée. L'ancien
CER strict ne doit plus être présenté comme la seule mesure opérationnelle.
