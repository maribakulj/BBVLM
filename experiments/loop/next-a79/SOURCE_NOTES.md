# A79 — résumés séparés, consultation 28 septembre 2026

## Zhao et al., DocLayout-YOLO — arXiv:2410.12628v1, 16 octobre 2024
https://arxiv.org/html/2410.12628v1
Niveau lu : corps principal HTML, introduction, méthode, expériences et conclusion
(§§1–6) ; annexes non relues ici. Mesh-candidate BestFit synthétise DocSynth-300K
par placement de blocs ; GL-CRM adapte les champs réceptifs à plusieurs échelles.
Le papier rapporte 70,3 mAP sur D4LA, 79,7 sur DocLayNet et85,5 FPS sur A100.
Ce sont des métriques de régions, pas de mots/lignes ni un CER, et ces latences
GPU ne prédisent pas notre coût CPU. DocStructBench porte surtout sur documents
académiques, manuels, analyses de marché et financiers ; presse historique à
vérifier séparément. Code : https://github.com/opendatalab/DocLayout-YOLO .
Apport BBVLM : un étage visuel de blocs peut fournir une contrainte de propriété
pour les lignes sans OCR complet. A79 utilise les poids existants et mesure son
effet réel, sans assimiler les régions aux articles ou aux colonnes parfaites.

## Sun et al., PP-DocLayout — arXiv:2503.17213v1, 21 mars 2025
https://arxiv.org/abs/2503.17213
Niveau lu : abstract et notice seulement. Famille de trois détecteurs,23 classes ;
la version L emploie RT-DETR-L. L'abstract annonce90,4 % mAP@0.5 et13,4ms/page
sur T4 pour L ; S annonce14,5ms CPU. Ces chiffres ne sont ni comparables à nos
IoU de lignes ni une validation sur presse historique. Code annoncé par les
auteurs via https://github.com/PaddlePaddle/PaddleX (lien vérifié), code non inspecté dans cette
itération. Piste de remplacement si un défaut YOLO de région est mesuré ; aucune
installation ni inférence PP-DocLayout, aucune revendication de supériorité locale.

## Code actuel DocLayout-YOLO
https://github.com/opendatalab/DocLayout-YOLO/blob/main/doclayout_yolo/models/yolov10/predict.py
Fonction postprocess réellement lue : sorties one2one, filtrage par confiance et
classes, remise à l'échelle des boîtes vers l'image originale. Pas d'ordre de
lecture, de colonnes ou de texte produit par ce code. Les paramètres de notre
forward restent ceux d'A66 à1024 ; le coût est payé une fois par page.
