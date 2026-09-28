
## A62
`experiment_queue.py` ajoute DAG durable, ressources, empreintes et claims externes. Le lanceur historique délègue à cette file après libération du verrou. Tests de processus réels dans tests/test_experiment_queue.py. Conventions et limites : CONTINUOUS_LOOP.md.

## A63
prepare_residual_a63.py :6lignes sélectionnées post-score, coordonnéesmm10→300ppi, crops natifs et ×3nearest. evaluate_residual_a63.py :IDs/images/hashes stricts, métriques inchangées, aucune réparation de référence. Tâches effectivement exécutées via queue.json.
