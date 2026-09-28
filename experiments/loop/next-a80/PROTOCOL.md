# A80 — transfert figé de la contrainte YOLO

Quatre pages Training inédites pour ces expériences, une par strate1600–1749,
1750–1849,1850–1900,1901–1945 ; plus petit SHA256(A80-v1:<nom>), exclure toutes
les pages A69/A74/A76 et la faute de nom officielle absente de l'inventaire.
La sélection utilise uniquement les noms de fichiers.100 Test intacts.
Indépendance de cette sélection vis-à-vis de nos réglages, pas preuve d'absence
de ces images dans l'entraînement des modèles tiers.

Algorithmes strictement inchangés : A76 dense Eynollah à largeur2000 puis
composantes8-connexes>=4px ; A79 DocLayout-YOLO1024/conf.2/maxdet300 ; propriétaire
unique avec90 % de surface de boîte ; A78 liens mutuels bornés à l'intérieur
d'une région. Les seules adaptations de scripts sont les noms/dossiers A80.
Sceller les prédictions avant XML pour chaque étage. Le score de la baseline
peut être produit avant le routeur, mais aucun paramètre du routeur ne change.

Critère LOCAL de transfert : précision ET rappel IoU50>=baseline pour CHAQUE
page et gain total de correspondances>0. Rapporter aussi IoU70 et le coût payé
Eynollah+YOLO ; pas d'OCR. Les critères globaux restent inchangés, aucune
prétention à des boîtes parfaites, aucun ajustement après score.
En cas d'échec, rejeter la règle ; en cas de succès, évaluer effet OCR/OLR sur
nouveau protocole, sans transformer cette mesure de lignes en validation de mots.
