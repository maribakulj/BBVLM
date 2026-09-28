# A58 — audit de 801 annotations Chronicling Germany

**371 575 TextLine, 0 Word, 0 Glyph** : les mots annoncés dans le papier sont des tokens, pas des boîtes de mots. 19 343 TextRegion, 11 506 SeparatorRegion, 1 306 TableRegion, 296 GraphicRegion, 63 ImageRegion. Les 32 514 régions et 371 575 lignes actuelles diffèrent des 32 451 / 371 642 du papier : citer la révision exacte.

456 Coords et 341 Baseline contiennent des points hors des dimensions déclarées ; 8 polygones dégénérés. Aucun ID dupliqué ni référence région pendante. Ce sont des alertes structurelles, à vérifier sur les images.

Splits : 651 train, 50 validation, 100 test dont 20 OoD ; splits principaux disjoints et cinq titres OoD absents de train/validation. **Une faute dans le split officiel** : Training contient `Koelnische_ZeiOut of distributiontung_1924_0035`, absent des XML ; `Koelnische_Zeitung_1924_0035` existe mais n’est assigné à aucun split. Aucune correction silencieuse. Les 100 pages test sont réservées ; aucune image ni valeur de transcription inspectée pour cette sélection.

Source : 60 036 720 octets téléchargés ; les 801 blobs XML reconstruisent exactement l’arbre Git publié, vérifié à la révision 66b50f53ccdb581d29cc02f670e469bbf583e825. Empreintes par fichier conservées.

Décision : retenir les régions comme référence candidate, texte à auditer selon ses conventions. Ne pas certifier les boîtes de mots ni l’ordre de lecture avec ce corpus. Le papier indique double contrôle des régions, simple correction du texte, correction sélective des lignes, ordre automatique non corrigé. Statuts Transkribus : 661 IN_PROGRESS,111 DONE,13 GT,13 NEW,3 autres/absents ; ce n’est pas une certification.

Coût : ~15 s CPU, aucune passe OCR/VLM ni image téléchargée. Objectif global non atteint. Prochaine expérience : Sol sur résidus OCR A54, crops source, IDs aveugles ; développement consommé, pas nouvelle validation.
