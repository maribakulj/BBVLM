# A81 — OCR aveugle de crops prédits : contamination malgré une forte IoU

Une lecture Luna réelle sur8 cibles/16 vues : six propositions appariées à une
référence et deux fragments sans référence appariée. Les six cibles obtiennent
79/331 éditions strictes,68/332 search_v1,56/272 lexical_alnum ; quatre sont
exactes dans les deux vues normalisées. Ce score diagnostique est conditionné
par une sélection oracle et le périmètre de transcription ; ce n'est pas le CER
d'une page ou d'un système validé. Les deux fragments restent non évaluables,
avec abstention `[illegible]`, pas de faux texte de référence vide.

Défaut mesuré : V243d7aaa a96,86 % IoU de rectangle mais contient deux lignes
voisines. L'attribution Otsu aux polygones PAGE place45,19 % de son encre dans
d'autres lignes hors du polygone assigné. C'est un proxy dépendant des annotations,
confirmé visuellement par l'agent principal, pas une vérité pixel parfaite.
La consigne «texte du rectangle» et la comparaison à une seule ligne ne coïncident
pas : Luna a aussi ajouté la suite visible en contexte. Ne pas attribuer toute
la distance à des erreurs de reconnaissance, ni compter une forte IoU comme
preuve d'un crop sûr. Sur Vde9f1e1c, les erreurs nem→nen et Brey→Bree sont visibles.

Escalade justifiée : Sol neuf,3 cibles/6 vues, aucune réponse Luna/GT exposée.
Consigne explicite de lire uniquement la ligne principale, deux échecs + un
contrôle. Sol obtient0/126 éditions lexicales sur ces trois lignes ; il subsiste
une différence d'espace dans search_v1. Modèle ET consigne ont changé : impossible
d'attribuer causalement le gain à l'un seul. La sélection est post-score ; aucune
revendication de0 % indépendant, aucun remplacement des XML ou des scores initiaux.
Les avis Luna de «clipping» aux bouts de phrases ne sont pas une mesure fiable
des glyphes coupés ; Sol distingue mieux ce point mais ne vaut pas adjudication.

Coût : une session Luna16images et une Sol6images. Tokens/prix non exposés.
Zéro nouvelle inférence CPU ; extraction des crops et audit d'encre seulement.
Tous IDs/images/hashes vérifiés ;100Test intacts ; sept gates globaux faux.

Suite : isoler/rectifier une ligne à partir de la géométrie PRÉDITE, éventuellement
avec le seul cropper PERO, puis mesurer encre perdue/contamination et OCR avant
un nouveau gel indépendant. Ne pas payer la reconnaissance PERO complète pour
utiliser son remappage. Préserver également les minuscules fragments en évidence
au lieu de les déclarer lignes lisibles ou de les effacer sans audit.
