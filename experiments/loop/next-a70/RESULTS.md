# A70 — les échecs profonds sont des absences, pas des fragments fusionnables

Sur les dix pages A69 consommées, 71 lignes avaient une couverture inférieure à
50 % par la meilleure boîte native. L'union de toutes les boîtes texte scellées
n'en récupère aucune à 95 % et une seule partiellement (75,45 %). Les 70 autres
restent sous 50 % ; 63 n'ont aucune boîte contributive couvrant au moins 1 %.

| attribution gelée | lignes | part |
|---|---:|---:|
| fragment récupérable par union (≥95 %) | 0 | 0,0 % |
| fragmentation partielle (50–95 %) | 1 | 1,4 % |
| absence détecteur ou divergence de convention (<50 %) | 70 | 98,6 % |

La page 1700 concentre 25 échecs, 1866 en concentre 15, 1924 onze et 1917 dix.
Une fusion post-détection est donc rejetée : elle ne peut corriger que 1/71 cas
profonds, et une union globale ferait en outre perdre la propriété de région.

Décision : A71 ne doit ni retuner `ink_crossing` ni ajouter une fusion ad hoc.
Il doit inspecter visuellement un échantillon opaque de lignes sans aucune boîte
pour séparer (a) texte réellement manqué, (b) rôle hors classes texte du modèle,
(c) convention PAGE discutable. Selon ce verdict, tester un rappel structurel
léger (colonnes/connected components/Eynollah) ou pivoter vers OLR. Aucun gate
scientifique n'est promu.

Coût : 2,01 s CPU, zéro nouvelle inférence, OCR ou VLM, 100 Test fermées. Le
premier job a échoué avant calcul faute de Shapely dans le Python minimal ; le
retry documenté a utilisé le venv CPU épinglé.
