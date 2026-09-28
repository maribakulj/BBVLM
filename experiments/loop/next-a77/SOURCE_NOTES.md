# A77 — sources et portée de lecture

## Boillet, Kermorvant & Paquet — 2022
*Robust Text Line Detection in Historical Documents: Learning and Evaluation Methods*,
arXiv:2203.12346 (v1 du 23 mars 2022 ; notice v2 identifiée).
Source primaire : https://arxiv.org/abs/2203.12346

Le texte intégral a été lu lors de A76 (résumé conservé dans next-a76/SOURCE_NOTES.md).
Cette reprise A77 a relu l’abstract primaire ; les accès HTML v2/ar5iv ont échoué.
Ne pas présenter cette reprise comme une nouvelle lecture intégrale.
Comparaison Doc-UFCN/dhSegment/ARU-Net, harmonisation des annotations et évaluation
pixel/objet/effet sur la reconnaissance. La diversité des conventions et des
corpus limite une conclusion tirée de l’IoU seule. Apport A77 : séparer contact
de rectangles, partage des pixels du masque et attribution réelle à une ligne.
Aucun résultat publié n’est assimilé à notre résultat local ; aucun modèle installé.

## Code primaire Eynollah — consulté le 28 septembre 2026
https://github.com/qurator-spk/eynollah/blob/main/src/eynollah/utils/separate_lines.py
Dernier commit touchant ce fichier : 42d383920d7c8cd2cab435e93ecb78b7661e5c77
(27 juillet 2026, correction des angles de deskew sur page paysage).
Sections réellement inspectées : separate_lines, dedup_separate_lines,
separate_lines_new2, do_work_of_slopes_new_curved. Profils lissés gaussiens,
pics/vallées, estimation d’espacement, deskew local et morphologie interviennent
avant les contours finaux. Notre règle A75/A76 omet ces opérations : son échec
ne constitue donc pas un benchmark du pipeline Eynollah complet.
A77 ne copie pas ces heuristiques et ne les règle pas sur A76 ; il mesure d’abord
si la fragmentation/fusion supposée est réellement compatible avec les pixels.
