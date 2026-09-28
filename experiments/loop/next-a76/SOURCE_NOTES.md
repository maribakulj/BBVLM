# Sources A76

## Boillet, Kermorvant & Paquet (2022), texte intégral

- **Référence/version :** *Robust Text Line Detection in Historical Documents:
  Learning and Evaluation Methods*, arXiv:2203.12346, version consultée le
  28 septembre 2026.
- **Niveau lu :** texte intégral HTML : méthode, jeux, protocoles, résultats et
  discussion ; pas seulement l'abstract.
- **Méthode :** étude de Doc-UFCN, dhSegment et ARU-Net sous annotations de
  lignes harmonisées. Les auteurs montrent que des polygones qui se touchent
  peuvent produire des lignes fusionnées et que le biais de convention de la
  vérité terrain affecte fortement l'apprentissage et l'évaluation.
- **Évaluation :** métriques objet, mean AP sur plusieurs seuils et évaluation
  orientée tâche par CER/WER d'un HTR ; l'IoU pixel seule est insuffisante.
- **Limites :** les résultats portent sur leurs corpus/modèles et ne démontrent
  ni boîtes ALTO parfaites ni CER nul ; les conventions doivent être harmonisées
  avant de comparer les systèmes.
- **Code :** les architectures et protocoles sont décrits ; aucun nouveau dépôt
  ni poids n'est installé en A76, car l'expérience teste une règle Eynollah déjà
  mesurée et figée.
- **Apport BBVLM :** ajoute un seuil **par page** pour éviter qu'une moyenne
  masque un échec local, maintient IoU50/70 séparés et interdit de confondre la
  géométrie avec l'impact OCR.
- **Source primaire :** https://arxiv.org/abs/2203.12346 .
