# A83 — code et littérature primaire,28septembre2026

Kodym & Hradiš, arXiv2102.11838v1,23février2021 : abstract relu en A82, résumé
séparé dans PAPER_SUMMARIES.md. Billet PERO Document textline extraction17juin2019
lu intégralement A82 ; baselines,hauteurs et remappage selon normales. Pas de nouvel
article intégral prétendu ici.

Code actuel `pero_ocr/document_ocr/page_parser.py` consulté sur GitHub :
https://github.com/DCGM/pero-ocr/blob/master/pero_ocr/document_ocr/page_parser.py
Sections effectivement lues : LayoutExtractor, LineCropper, PageParser, factories.
Dernier commit fichier vérifié11eb20ea1e9653abdd7fc1c92b856cef782c9edc,
21février2024. Les quatre RUN_* commandent indépendamment création/exécution des
étages. Config d'origine0.7.0 inspection locale ; numpy1.26.4 conservé, pas de
réinstallation OpenCVGUI ni torchGPU. NumPy2 du dry-run a été refusé en faveur
d'une installation explicite sans dépendances et versions documentées.

`torch_parsenet.py` installé réellement lu (get_maps et get_maps_with_optimal_resolution) :
un appel réseau peut être suivi d'un second si hauteur médiane hors intervalle9–15
et changement d'échelle suffisant. L'état last_downsample est conservé entre pages.
C'est pourquoi nous comptons les vrais appels, au lieu d'annoncer «une passe/page».
`crop_engine.py` lu A81 : aucun modèle n'est nécessaire au seul remappage une fois
baseline/hauteurs disponibles. La version de paquet est0.7.0, distincte d'une
promesse d'identité bit-à-bit avec master ; empreintes locales dans les artefacts.
