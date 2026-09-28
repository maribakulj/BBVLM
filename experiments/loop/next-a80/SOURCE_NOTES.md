# A80 — sources et portée

Hypothèse inchangée issue A79, pas nouveau réglage. Le code primaire réellement
relu en A79 est DocLayout-YOLO `models/yolov10/predict.py` : filtrage confiance,
classes et coordonnées natives ; aucune garantie de colonnes/articles parfaits.
https://github.com/opendatalab/DocLayout-YOLO/blob/main/doclayout_yolo/models/yolov10/predict.py
Article Zhao et al., arXiv:2410.12628v1,16 octobre2024 : corps principal lu A79,
MeshCandidate/GL-CRM, scores région et coût GPU non transférables aux lignes CPU.
Voir le résumé séparé A79 dans PAPER_SUMMARIES.md.

Deux nouvelles lectures primaires sont consignées séparément ci-dessous pour
la prochaine évaluation OCR ; aucun changement des normalisations figées.

## Rigal et al. — Benchmarking Vision-Language Models for French PDF-to-Markdown Conversion
arXiv:2602.11960v1, 12 février 2026. https://arxiv.org/html/2602.11960v1
Lu le 28 septembre2026 : corps principal HTML, sections1–7 ; pas simple abstract.
À partir de60 000 documents CCPDF/Gallica français, sélection de pages difficiles
par désaccord dotsOCR/MinerU. Des tests produits avec Gemini3Pro puis revus par
humains évaluent présence de texte, ordre et tableaux, avec normalisations par
catégorie. Les pages multicolonnes et dégradées restent difficiles ; augmenter
le DPI n'améliore pas monotonement vitesse et qualité. Les sorties répétitives
sur petit texte sont un défaut utile à suivre. Les scores sont des taux de tests,
pas un CER, et ne démontrent pas «zéro erreur» sur nos corpus. Sélection difficile,
biais possible du générateur de tests, chevauchement de préentraînement inconnu.
Code annoncé : https://github.com/ld-lab-pulsia/vlmparse (non inspecté ici).
Apport BBVLM : garder profils de normalisation immuables, coût de génération,
OCR et ordre séparés. Aucun modèle installé ni score publié transposé.

## Gardella et al. — When Low CER is Not Enough
arXiv:2607.24077, 27 juillet2026. https://arxiv.org/abs/2607.24077
Lu le 28 septembre2026 : abstract primaire seulement via recherche ; ouverture
directe échouée. Étude de systèmes OCR/VLM sur microfilms historiques uruguayens
Berrutti : malgré de meilleurs CER/WER, les VLM peuvent normaliser, ajouter ou
substituer sémantiquement du contenu, notamment des entités nommées. L'abstract
motive une typologie d'erreurs au-delà de la distance d'édition. Texte intégral,
code et résultats numériques non inspectés ; aucune supériorité quantitative
revendiquée. Apport BBVLM : conserver diplomatique/search/lexical séparés,
consigner les ajouts et substitutions, ne pas assimiler faible CER et fidélité.
