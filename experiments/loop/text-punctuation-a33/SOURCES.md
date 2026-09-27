# Sources primaires effectivement lues — A33

Consultées le 2026-09-27 avant le score final :

1. Source actuelle de Tesseract, `src/ccmain/tesseractclass.cpp`, lignes 185–210 :
   https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/src/ccmain/tesseractclass.cpp
   Le code expose `enable_noise_removal`, des seuils séparés pour diacritiques
   disjoints et nouvelle ponctuation, puis `chs_leading_punct`,
   `chs_trailing_punct1/2`. SHA-256 des octets lus :
   `3f3d0221682225a8c88f3a414dcf850271a2ff23b5a1baf80e0a4916094fca36`.
   Copie conservée dans `tesseractclass.cpp`. A33 reprend seulement l'idée
   d'une décision conditionnée par la ponctuation; il n'implémente ni le
   classifieur ni les certitudes Tesseract. La branche `main` est mobile.
2. Smith, Antonova et Lee (2009), *Adapting the Tesseract Open Source OCR
   Engine for Multilingual OCR*, sections 3.2–3.3 déjà lues pour A32 :
   https://tesseract-ocr.github.io/docs/MOCRadaptingtesseract2.pdf
   Les petites composantes sont rattachées au corps ou traitées comme bruit;
   les exceptions (dont les points) imposent de ne pas filtrer uniquement par
   taille. A33 teste précisément une information textuelle supplémentaire.
3. Tesseract actuel, `src/textord/makerow.cpp`, `dot_of_i` et
   `vigorous_noise_removal`, source et empreinte archivées en A32. La remarque
   du code — le test spécialisé ne couvre pas les autres diacritiques — interdit
   de généraliser le comportement aux accents français.

Limites : les ensembles A33 ajoutent guillemets/tirets français et `*`; ce sont
des choix BBVLM, pas des recommandations du papier ou de Tesseract. Le résultat
montre justement que `*` était une extension trop large. Aucun moteur lourd
installé, aucun score Tesseract comparé.
