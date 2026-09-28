# A81 — sources consultées le28 septembre2026

Articles : Rigal et al., arXiv2602.11960v1 (12février2026), corps principal relu ;
Gardella et al., arXiv2607.24077 (27juillet2026), abstract consulté A80, ouverture
directe encore échouée A81. Résumés séparés complets dans PAPER_SUMMARIES.md/A80.
Pas de nouvelle lecture intégrale revendiquée pour Gardella. Les normalisations
par catégorie de Rigal ne remplacent pas nos trois fonctions immuables.

Code primaire DocLayout-YOLO `models/yolov10/predict.py` relu intégralement :
https://github.com/opendatalab/DocLayout-YOLO/blob/main/doclayout_yolo/models/yolov10/predict.py
Le postprocess donne des rectangles natifs, sans isolation des lignes.

Code primaire PERO `pero_ocr/core/crop_engine.py` lu intégralement :
https://github.com/DCGM/pero-ocr/blob/master/pero_ocr/core/crop_engine.py
Dernier commit touchant le fichier vérifié : ce7be51ffaa38214c8927a3339bdbff4531877fb,
16février2024. `get_crop_inputs` suit une baseline interpolée et ses normales,
avec hauteurs au-dessus/au-dessous ; `fast_remap` interpole les pixels.
Ce composant n'exige pas en lui-même une passe du reconnaisseur. Cependant il
exige une baseline/hauteurs correctes ; notre contour prédit n'est pas déjà une
baseline, et ses paramètres par défaut32px ne sont pas automatiquement adaptés
aux VLM. Aucun remappage PERO exécuté en A81 ; piste motivée par contamination45,19 %.
