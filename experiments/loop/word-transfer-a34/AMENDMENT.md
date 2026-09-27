# Amendement mécanique après ouverture, avant score

Le premier lancement de l'évaluateur s'est arrêté avant chargement PERO et avant
tout score : `evaluate_french_holdout_a25.main()` attend la clé historique
`protocol_sha256`. A34 conservait déjà exactement cette empreinte sous
`sealed_sha256.protocol`, mais pas la copie au premier niveau. La même valeur
`1166e0…751f` a été ajoutée au manifeste. Aucun paramètre, travail, page, octet
source, algorithme ou seuil n'a changé; aucun rapport n'existait.

Conséquence procédurale : le SHA du manifeste n'est plus celui enregistré par
`opened.json`. Le rapport doit l'indiquer et ne pas prétendre que l'ensemble du
manifeste est immuable. La règle candidate et son code, eux, restent ceux gelés
et vérifiés avant l'ouverture. Un gate projet demeure impossible dans tous les
cas à cause du domaine allemand/livresque et des entrées oracle.

Deuxième arrêt, toujours avant rapport/score : PERO a produit une transcription
vide pour la petite ligne `P00000033_l111` (`E`). Son exporteur ALTO omet alors
la ligne et le binder strict refuse le décalage. L'adaptateur A34 représente
désormais explicitement ce cas comme une ligne identifiée avec zéro mot natif,
au lieu de décaler les IDs ou supprimer la référence. Les 42 autres lignes de
la page conservent les contrôles texte/ordre. La règle A32/A34 et ses seuils ne
changent pas. L'empreinte de l'évaluateur est donc amendée dans le manifeste;
le rapport dira `evaluation_adapter_amended_after_open_before_scores=true` et
ne prétendra pas que tout l'évaluateur fut gelé avant ouverture.
