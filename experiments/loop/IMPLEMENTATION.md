
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

## A65
`evaluate_crop_geometry_a65.py` mesure trois stratégies de masque sur les 50
Validation Chronicling avec Shapely 2.1.2. Hashes A58 vérifiés, 100 Test exclus,
aucun texte lu. Polygones invalides en quarantaine sans réparation. Quatre tests
synthétiques et monotonicité des surfaces conservées vérifiés. Report complet
avec IDs, SHA256, compteurs et coût ; aucune inférence détecteur/OCR/VLM.

## A66
`fetch_crop_pilot_a66.py` verifies mixed Git/LFS image content at immutable source
revision. `evaluate_predicted_crops_a66.py` performs ten real CPU forwards and
only then opens reference geometry; synthetic coverage tests and coordinate
invariants pass. All inputs and raw predictions retained. See next-a66/RESULTS.md
for failure/recovery records. REFERENCE_ADDENDUM.md is separate to preserve the
immutable A63 audit input. Restore five images with the fetch script; restore
the 40.7MB YOLO weight through restore_public_assets.py --only. No full PERO run.

## A67
Native crop/context/boundary evidence generated deterministically from four
consumed A66 metric-selected examples; opaque shuffled IDs, no transcript values
read. Actual Luna reader12views, targeted Sol6views. Strict response IDs and
image hashes verified. Crops only use outward integer rounding of raw YOLO boxes;
no resampling. Final report-v2 preserves separate reader observations and costs
unknown. No GT edits and no model-agreement truth criterion. Next: local ink-edge
repair comparison, with explicit contamination measure and fresh validation later.

## A68–A69
`extend_crop_edges_to_connected_ink` étend séparément chaque bord lorsqu'une
composante 8-connexe traverse une bande intérieure de deux pixels, avec aire
minimale 3 et contexte borné. A68, sur données consommées, motivait un transfert.
A69 applique exactement la même règle à dix pages Training gelées après écriture
et hash des prédictions image-only. Elle réduit l'aire ajoutée et la contamination
face au padding fixe, mais échoue au gate de couverture : 184→160 lignes sous
95 %, au lieu des ≤147 gelées. Le writer initial ayant échoué après les dix
forwards sur une métadonnée OpenCV, `score_transfer_a69_retry.py` réutilise les
artefacts scellés et fait zéro nouvelle inférence. Ne pas promouvoir cette règle.

## A70
`diagnose_deep_failures_a70.py` réutilise les boîtes A69 scellées et calcule,
pour chaque ligne sous 50 %, la couverture de la meilleure boîte et de l'union
des boîtes. Sur 71 résiduels, zéro est récupérable à 95 %, un seul est partiel
et 70 restent sous 50 %. Le retry venv est distinct du job initial échoué avant
calcul. Conclusion : ne pas implémenter une fusion de fragments globale.

## A71
`prepare_visual_misses_a71.py` choisit par hash 12 lignes à contribution nulle,
au plus deux par page, et génère des vues à identifiants opaques sans texte de
référence. `verify_visual_misses_a71.py` impose l'ensemble exact des IDs et
hashes avant d'agréger la réponse Luna. Le résultat 11 textes visibles, 1 ambigu,
5 récupérations rectangulaires sûres motive un pilote de segmentation de lignes,
mais ne constitue pas une annotation de boîte. Les vues, manifeste, réponse
brute et rapport sont conservés ; zéro page Test et zéro vérité terrain modifiée.

## A72–A76

`evaluate_textline_transfer_a76.py` réutilise l'étage natif A72/A74 Eynollah,
scelle tous les masques et composantes 8-connexes avant l'accès XML, puis fait
un appariement hongrois à IoU50/70. A76 emploie un nouveau gel Training à quatre
strates excluant A69/A74. La règle A75 échoue au transfert (P/R IoU50
.7274/.8613), surtout sur la mise en page dense de 1924. Conserver le masque
comme évidence ; ne pas émettre de boîtes ALTO générales à partir des seules
composantes connexes.
