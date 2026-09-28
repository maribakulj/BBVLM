# A82 — sources primaires,28septembre2026

## Kodym & Hradiš, Page Layout Analysis System for Unconstrained Historic Documents
arXiv:2102.11838v1,23février2021. https://arxiv.org/abs/2102.11838
Niveau lu : notice et abstract seulement ; HTML intégral indisponible lors de
cette consultation. Le CNN de détection des baselines est étendu pour prédire
hauteurs de ligne, frontières de blocs et orientation pixel. Évalué sur cBAD et
le nouveau jeu PERO layout. Pas de chiffre transféré à nos pages, ni preuve de
mots parfaits ou zéroCER. Code primaire pertinent : DCGM/pero-ocr, crop_engine.py
relu en A81. Apport BBVLM : distinguer la géométrie de ligne utile du reconnaisseur,
et mesurer les étages séparément. A82 n'exécute pas ce détecteur.

## PERO, Document textline extraction — billet technique17juin2019
https://pero.fit.vutbr.cz/post/2019-06-17_1_Textlines
Niveau lu : texte complet du billet. Une baseline et des hauteurs ascendante et
descendante définissent le crop. La remise à plat suit les normales de la ligne
pour éviter le texte voisin des rectangles inclinés. Ce billet illustre le
mécanisme ; il ne chiffre pas notre coût ni ne garantit une extraction sans perte.
Apport : notre contamination A81 est un défaut connu du rectangle, pas une preuve
que le VLM manque seul de capacité. Le code actuel `crop_engine.py` a été inspecté
avec dernier commit fichier ce7be51ffaa38214c8927a3339bdbff4531877fb (16février2024).

## Sources/code complémentaires
Eynollah, DocLayout-YOLO et Boillet2022 : voir les résumés A76/A79/A81.
La règle A82 masque des contours existants ; elle n'est ni le cropper PERO ni le
pipeline Eynollah complet. Aucun nouveau modèle installé. Recherche récente CURIO
WACV2026 repérée, PDF primaire403 : aucune lecture intégrale ni résumé scientifique
revendiqué de ce papier. Rigal2026/Gardella2026 déjà résumés séparément A80.
