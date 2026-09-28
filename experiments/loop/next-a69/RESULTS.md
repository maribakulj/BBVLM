# A69 — transfert gelé : la réparation par encre ne passe pas

La règle `ink_crossing` d'A68 a été transférée sans changement sur dix pages
Training officielles Chronicling Germany, couvrant 1617–1933 et dix titres.
Ces pages n'avaient jamais servi au détecteur ni au score de crops BBVLM ; A58
avait toutefois audité leur XML structurellement, donc ce test est un transfert
gelé, pas une validation de corpus pristine. Les 100 pages Test restent fermées.

Dix véritables passes DocLayout-YOLO CPU à 1024 px ont produit 1 768 lignes de
référence. Les prédictions et candidats image-only ont été enregistrés et hachés
avant ouverture des XML. Le premier writer a échoué *après* l'inférence sur le
nom de distribution `opencv-python`; le retry a réutilisé les dix prédictions
scellées et n'a exécuté aucun modèle.

| Politique | couverture moyenne | lignes < 95 % | lignes < 50 % | aire ajoutée | aire étrangère ajoutée | boîtes > 1 % intrusion |
|---|---:|---:|---:|---:|---:|---:|
| native rasterisée | 0,950775 | 184 | 71 | 0 | 0 | 0 |
| padding fixe | 0,961570 | 79 | 67 | 7 439 980 | 363 062 (4,88 %) | 82 |
| encre traversant le bord | 0,953738 | 160 | 68 | 1 161 501 | 25 301 (2,18 %) | 15 |

`ink_crossing` économise 84,4 % de l'aire du padding fixe, réduit fortement la
contamination absolue et n'abaisse la couverture moyenne d'aucune page. Mais il
ne réduit les lignes sous 95 % que de 13,0 % (184→160), sous le seuil gelé de
20 %. Le padding fixe atteint 57,1 % (184→79), au prix de 6,4 fois plus d'aire
ajoutée et 82 boîtes contaminées à plus de 1 %.

Le résiduel profond est structurel : 25/71 lignes sous 50 % se trouvent sur
`Reichs_Post_Reuter_1700-11-16_0001`, et ni le padding ni l'encre n'en corrigent
une seule. Les pages 1917 et 1924 concentrent aussi 21 lignes profondes, mais
les deux expansions n'en récupèrent que trois. Une extension de quelques pixels
ne peut donc pas réparer les régions manquantes, fragmentées ou associées au
mauvais parent.

Décision : règle rejetée comme politique de crop générale. Elle peut rester un
outil de proposition locale à faible contamination, sans promotion. A70 doit
classifier les 71 échecs profonds à partir des prédictions scellées et des
polygones consommés, puis choisir une réparation structurelle distincte
(fusion de fragments, région manquante ou convention d'annotation), sans
retuner A69 et sans ouvrir Test. Aucun des sept critères globaux ne change.

Coût : dix passes détecteur réelles, zéro OCR, zéro VLM, zéro nouvelle passe au
retry. Les originaux et références sont inchangés.
