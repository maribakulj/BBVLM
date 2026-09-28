
## A62
`experiment_queue.py` ajoute DAG durable, ressources, empreintes et claims externes. Le lanceur historique délègue à cette file après libération du verrou. Tests de processus réels dans tests/test_experiment_queue.py. Conventions et limites : CONTINUOUS_LOOP.md.

## A63
prepare_residual_a63.py :6lignes sélectionnées post-score, coordonnéesmm10→300ppi, crops natifs et ×3nearest. evaluate_residual_a63.py :IDs/images/hashes stricts, métriques inchangées, aucune réparation de référence. Tâches effectivement exécutées via queue.json.

## A64
`src/bbvlm/hipe_metrics.py` reproduit l'ordre exact de normalisation du scorer
HIPE-OCRepair 0.9.9 et calcule H/S/D/I puis le MER. Le backtrace local a été
comparé à `jiwer.process_characters` sur 64 couples réels A54 : 64/64 comptes
identiques. `scripts/evaluate_hipe_projection_a64.py` reconstruit PERO, Luna
brut, la garde et l'abstention depuis les artefacts scellés A54 ; il ne lance
aucun modèle et ne modifie aucune référence. `scripts/verify_hipe_alignment_a64.py`
matérialise la vérification d'équivalence. Trois tâches A64 sont tracées dans
la file ; A65 reste une préparation distincte géométrie/OLR.
