# A62 — enchaîner les tâches prêtes pendant la session

Défaut constaté dans le code : liste CPU historique fixe, arrêt au premier échec, aucune file de dépendances externe. Cela ne justifie pas une pause entre expériences, mais rendait la reprise fragile et peu exploitable.

Ajout `experiment_queue.py`, file persistante, verrou commun, empreintes, reçus, quotas CPU/fichiers/VLM, délais maximaux et actions externes explicitement réservées. Intégration dans `autonomous_loop.py --execute`. Les VLM restent de vrais sous-agents lancés par Codex actif. Aucun modèle ou résultat n'est simulé par le dispatcher.

**9 tests réussis** en 0,794 s : dépendances avec concurrence réelle, isolation des échecs, artefacts absents/JSON invalide, reprise sans réexécution, inputs et outputs altérés, claims externes exclusifs et périmés, reprise après perte de coordinateur, verrou partagé, dépassement de délai et DAG invalide. Le test A57 de conservation du checkpoint passe également.

Deux tâches réelles de maintenance terminées par la file : suite de tests et fixité des trois images A61 (toutes identiques à A60). Chevauchement enregistré : 0,058 s. L'appel intégré au lanceur historique, puis une nouvelle inspection, ne relancent aucune commande terminée. Ces chiffres vérifient l'orchestration ; ils ne sont ni une mesure d'accélération OCR, ni un résultat CER.

Branche Claude relue le 2026-09-28 : JOURNAL I01 inchangé, SHA ba685e9b4c870e245d1d201381986178660abb4c. Aucun résultat scientifique adopté ou fusionné. A63 préparation exposée comme prochaine action de l'agent ; aucune attente horaire dans le runner. En cas de session interrompue, l'état permet une reprise mais ne garantit pas une présence permanente du modèle.

Les sept critères scientifiques demeurent faux. Coût : zéro appel VLM, aucune installation lourde. Source de cette modification : inspection et tests du code local, pas une nouvelle hypothèse de reconnaissance nécessitant un article expérimental.
