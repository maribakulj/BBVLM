# A79 — YOLO comme contrainte de regroupement

Développement consommé A76, gel 28 septembre 2026 avant nouvelles inférences.
Défaut justifiant le coût : A78 a relié des colonnes distinctes et perdu360
correspondances. Une région prédite devrait bloquer ces jonctions.

4 forwards CPU DocLayout-YOLO, poids A66 inchangés/hachés, imgsz1024, conf0.2,
max_det300, 4threads. Pas de nouveau téléchargement/modèle ni de grille de seuils.
Exclure les classes figure3/table5 comme A66. Chaque composante initiale est
attribuée à une région seulement si UNE région contient >=90 % de sa surface
rectangulaire. Si zéro ou plusieurs régions conviennent, conserver la composante
seule. Appliquer A78 inchangé à chaque groupe de propriétaire unique ; garder
les inconnues. Pas de clipping aux régions YOLO et aucune composante supprimée.

Persister predictions.json puis candidates.json avant accès aux XML. Mesurer
IoU50/70, gains/pertes par référence, coût détection et total. Critère local :
aucune baisse de précision ou rappel IoU50 par page face à A76, gain total>0.
Comparer aussi à A78 sans lui accorder le rôle de baseline principale.
Ne pas régler en cas d'échec, ne pas appeler cette analyse validation indépendante.
Aucun OCR, VLM ou Test ; aucune modification des originaux. Les régions YOLO
sont des blocs proposés, pas des colonnes ni articles certifiés.
