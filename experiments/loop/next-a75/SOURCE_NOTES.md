# Sources A75

## Kodym & Hradiš — *Page Layout Analysis System for Unconstrained Historic Documents*

- Version/date : arXiv:2102.11838, 23 février 2021.
- Niveau lu : texte intégral HTML, méthode, post-traitement, expériences PERO et
  évaluation OCR ; pas seulement l'abstract.
- Méthode : ParseNet prédit baseline, extrémités, hauteurs ascender/descender et
  frontières de blocs. Les baselines deviennent des splines puis des polygones
  par offsets perpendiculaires ; le groupement en blocs est séparé.
- Résultats : F1 baseline cBAD 0,902 avec adaptation d'échelle, fusion et
  orientations ; sur PERO, P/R/F ligne polygonale 0,811/0,813/0,804 à IoU>0,7.
- Limites : deux inférences pour l'échelle adaptative, environ 5 Go GPU pour une
  image de 5 Mpx ; un cas journal fusionne deux blocs et toutes leurs lignes ;
  les métriques géométriques ne prédisent pas parfaitement l'effet OCR.
- Code/données : jeu PERO public lié ; aucun nouveau poids ni outil installé.
- Apport BBVLM : seuil IoU70 motivé, appariement d'instances et séparation
  explicite baseline/polygone/bloc. A75 ne prétend pas reproduire ParseNet.
- Source : https://arxiv.org/abs/2102.11838 .

## Code Eynollah courant

Le même `separate_lines.py` officiel inspecté en A74 est la source logicielle :
le code fait densité, séparation, deskew et contours avant dilatation. A75 teste
la propriété la plus minimale visible du modèle 2024 — instances 8-connexes du
masque complet — sans copier les seuils complexes ni installer le pipeline.

