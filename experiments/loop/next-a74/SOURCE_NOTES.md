# Sources lues pour A74

## Schultze et al., *Chronicling Germany* (texte intégral)

- Version : arXiv:2401.16845v3, 25 octobre 2024.
- Lecture : texte intégral HTML, notamment jeu de données, résultats de détection
  de baseline, limites et protocole d'annotation.
- Méthode : 693 pages de journaux historiques allemands ; régions polygonales,
  lignes/baselines et texte PAGE-XML ; U-Net de baseline avec objectif conjoint
  ligne/bloc ; entraînement sur crops 256×256 et augmentations.
- Résultat pertinent : F1 de baseline annoncé autour de 0,9 ; les auteurs disent
  explicitement ne pas avoir annoté de boîtes texte et ne pas pouvoir comparer
  correctement aux pipelines de détection directe d'objets texte.
- Qualité/limites : layout relu par un second expert, mais transcription corrigée
  pour l'instant par une seule personne et seconde passe annoncée ; biais fort
  vers la Kölnische Zeitung ; généralisation layout jugée insatisfaisante.
- Code/données : code Chronicling Germany et dépôt GitLab du corpus sont liés par
  l'article. A74 utilise la révision publique déjà épinglée par A66.
- Apport BBVLM : justifie de traiter les baselines/lignes comme preuve distincte
  des boîtes ALTO et interdit d'appeler les polygones une vérité parfaite.

## Code Eynollah courant (inspection primaire de l'implémentation)

- Révision inspectée : branche `main`, arbre GitHub
  `15ddb7750e132462321a3d57b2a2b74cb8f2b151`, 28 septembre 2026.
- Fichier lu : `src/eynollah/utils/separate_lines.py` (texte complet récupéré,
  sortie d'affichage tronquée mais sections `separate_lines`,
  `textline_contours_postprocessing`, `separate_lines_new2` et
  `do_work_of_slopes_new_curved` inspectées).
- Méthode : projection de densité, lissage gaussien, pics/vallées, deskew local,
  morphologie et contours par région ; ce n'est pas une simple boîte englobante
  de composante.
- Limites : nombreux seuils et branches historiques ; dépendance aux régions
  parentes et au deskew ; importer le pipeline complet ajouterait des passes et
  dépendances qui ne sont pas encore justifiées par A74.
- Code : dépôt officiel `qurator-spk/eynollah`, pas installé dans A74.
- Apport BBVLM : A73 a justement échoué parce qu'il réduisait directement une
  composante dense à un rectangle. A74 vérifie d'abord, sur données nouvelles,
  que le masque dense mérite un futur séparateur ligne inspiré de ce code.

