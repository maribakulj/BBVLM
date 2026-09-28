# A73 — boîtes des composantes non couvertes : rejet

La règle image-only conserve 63 composantes du masque A72 dont au moins la
moitié des pixels est hors des rectangles YOLO. Elle récupère les 33/33 lignes
A70 sans contributeur à au moins 50 % : le rappel est confirmé.

La conversion directe en rectangles échoue pourtant deux gates de précision :

- 25/63 propositions ont moins de 1 % de leur aire dans une ligne PAGE ;
- 56,33 % seulement de l'union des rectangles proposés tombe dans l'union des
  lignes, sous le seuil gelé de 75 %.

La page 1700 concentre les 25 faux positifs parmi 53 propositions ; la page 1924
n'en a aucun parmi 10, mais ses rectangles englobent beaucoup d'espace : 35,53 %
seulement de leur union appartient aux lignes. Le gate local global échoue.

Décision : ne pas retuner l'aire, le ratio hors YOLO ou les morphologies sur ces
pages consommées. Conserver A72 comme signal dense de rappel, rejeter la boîte
englobante de composante comme production ALTO. La suite doit extraire une ligne
centrale/baseline de manière principielle puis la tester sur un nouveau gel
divers, ou avancer un axe OLR/retrieval indépendant.

A73 réutilise les masques et prédictions scellés : zéro nouveau forward, zéro
OCR, zéro VLM, zéro page Test. `candidates.json` a été écrit et haché avant
l'ouverture des XML. Aucun gate global n'est modifié.
