# A34 — validation indépendante de transfert des boîtes

Gel avant ouverture des pages, 2026-09-27. Aucune autre page française à boîtes
`Word` n'existe dans le dépôt SBB : les huit ont été consommées. Les corpus
français DAHN/TAPUS et Reichsanzeiger-GT ont été inspectés seulement sur un
exemple exclu : ils donnent des lignes mais aucun nœud `Word`. Ne jamais
convertir leur tokenisation textuelle en fausse GT géométrique.

Sélection déterministe dans OCR-D/OCR-D-GT-VD-SBB, révision
`481f7235acfc1f78e88b3c2f22f551595c3f2032` : exclure tous les travaux déjà
ouverts A18/A25/A28, garder les travaux à exactement quatre paires PAGE/TIFF,
classer par SHA-256 de `A34-independent-transfer:` + identifiant et prendre les
trois premiers. Le script de gel ne lit que l'arbre Git. Les douze pages sont
donc indépendantes du réglage A32/A33, mais probablement allemandes/latines et
livresques : validation de transfert géométrique, jamais preuve presse française.

Candidats gelés : Otsu brut A28; A32 corps+satellites inchangé; A34 conservateur,
qui applique A33 uniquement aux signes finaux sauf `*`, avec aire minimale 20
pixels. Tous les autres seuils A33 restent inchangés. Ce choix provient de
l'audit A33 consommé et est gelé ici avant octets PAGE/image et avant scores.

Entrées oracle : rectangles/polygones de ligne, transcription et nombre/ordre
des tokens. Le CTC PERO est recalculé sur CPU; aucune passe VLM. Comparer PERO
natif, CTC forcé, Otsu, A32, A34; rapporter OCR natif, IoU50/80, IoU moyen,
erreurs de frontières, chaque page/travail, temps et tous changements A34.
Gate local A34 : aucun token omis; au moins un gain; aucune régression appariée;
IoU moyen et rappel IoU80 non inférieurs à A32 dans chacun des trois travaux.
Même si ce gate passe, aucun gate projet ne passe : langue/domaine, lignes et
texte oracle, GT externe non ré-adjudiquée et baseline synthétique.
