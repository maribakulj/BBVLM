# A64 — résultat de la projection HIPE-OCRepair

Expérience terminée sans nouvelle inférence OCR, VLM ou détecteur. Les seize
blocs A54 gelés et déjà consommés ont été rescorrés avec la normalisation et le
cMER du scorer HIPE-OCRepair 0.9.9 au commit
`d1e76e447629ea9cf8dead32ae3c44b0d48d77b3`. L'implémentation locale reproduit
exactement les comptes H/S/D/I de `jiwer.process_characters` sur les 64 couples
réels (16 blocs × 4 sorties), zéro désaccord.

| Sortie | erreurs HIPE | dénominateur | micro-cMER | blocs exacts | mieux/égal/pire que PERO |
|---|---:|---:|---:|---:|---:|
| PERO | 74 | 11 661 | 0,6346 % | 3/16 | — |
| Luna brut | 35 | 11 653 | **0,3004 %** | 6/16 | 9 / 5 / 2 |
| Luna gardé | 46 | 11 653 | 0,3947 % | 6/16 | 7 / 7 / 2 |
| Luna gardé + abstention | 46 | 11 653 | 0,3947 % | 6/16 | 7 / 7 / 2 |

La normalisation explique une partie importante de l'écart avec le CER strict,
mais ne produit pas 0 %. Les deux régressions Luna sont informatives : T005
transforme `leviatban` en `leviathan` face à une référence `leviatbau`, et T016
transforme `personelle` en `personnelle`. La première ressemble fortement à une
correction sémantique plausible contre une référence fautive ; la seconde peut
être une modernisation non diplomatique. Elles restent des désaccords tant que
l'image n'est pas adjudiquée indépendamment. Aucun original n'a été modifié.

La garde locale réduit les corrections utiles sur T008 et T010 sans supprimer
les deux régressions. Elle reste donc moins bonne que Luna brut sur cette vue,
mais cette comparaison postérieure ne permet pas de retuner la garde sur A54.

Coût CPU mesuré : 53,05 s pour vérifier 64 alignements contre jiwer et 51,07 s
pour la projection complète ; zéro passe modèle. Les vues
`strict_nfc_diplomatic`, `search_v1`, `lexical_alnum` et HIPE restent séparées.
A54 est consommé : A64 n'ajoute aucune preuve indépendante de généralisation,
de géométrie, d'OLR, de métadonnées ou de retrieval. Tous les gates globaux
restent fermés.
