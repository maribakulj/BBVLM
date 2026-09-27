# Sources primaires effectivement consultées le 2026-09-27

1. Smith, Antonova et Lee (2009), *Adapting the Tesseract Open Source OCR
   Engine for Multilingual OCR*, sections 3.2 et 3.3, texte PDF lu :
   https://tesseract-ocr.github.io/docs/MOCRadaptingtesseract2.pdf
   Les petites composantes peuvent être diacritiques ou bruit; rattachement
   aux composantes du corps et attribution aux lignes. La hauteur des caractères
   est estimée statistiquement. Cela motive l'ablation mais n'en fournit pas
   les seuils : notre bande de densité n'est pas leur algorithme complet.
2. PERO, `pero_ocr/core/layout.py`, branche master récupérée ce jour :
   https://raw.githubusercontent.com/DCGM/pero-ocr/master/pero_ocr/core/layout.py
   Fonction d'export ALTO, lignes 488–558 lues : alignement de logprobs, portée
   temporelle des mots, `EngineLineCropper.get_crop_inputs`, extrema du mapping
   pour HPOS/VPOS/WIDTH/HEIGHT; ce n'est pas une délimitation par encre.
   SHA256 `d36724b4851ab39cd69d73b8a536a9438d59000097ec7fe39e1d3ab9c0fd5661`.
   Copie exacte conservée dans `sources/pero-layout.py`; code installé comparé.
3. Tesseract, `src/textord/makerow.cpp`, branche main récupérée ce jour :
   https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/src/textord/makerow.cpp
   `dot_of_i` et `vigorous_noise_removal`, lignes 400–555 lues. La fonction
   spécialisée protège certains points de i mais précise ne pas traiter les
   autres diacritiques. L'élagage par taille seul est donc une ablation, pas
   une solution générale aux accents français. Cette fonction n'est pas
   nécessairement active dans toute configuration Tesseract.
   SHA256 `a92eeebe8a93b599a742cf0b96077675c50d841bfe9533fba77802f108a84785`.
   Copie exacte conservée dans `sources/tesseract-makerow.cpp`.

Les branches sont mobiles; les empreintes identifient les octets réellement
lus. Aucun nouveau moteur lourd installé. Les seuils A32 sont nos choix de
développement explicites, pas des performances ou recommandations attribuées
aux auteurs. Les pages A28 restent consommées.
