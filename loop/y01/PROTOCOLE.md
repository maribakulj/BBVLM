# Y01 — pré-segmentation en zones par un détecteur YOLO (régions OLR)

Figé le 01/10 avant toute inférence sur nos pages. Demande du mainteneur (« placer un YOLO pour une pré-segmentation »). Littérature : L51-L54.

Détecteur : `tuandunghcmut/doclaynet-yolo26l` (YOLO26-L, ultralytics, DocLayNet v1.2 ; classes 1-10 = Caption, Footnote, Formula, List-item, Page-footer, Page-header, Picture, Section-header, Table, Text ; classe 0 ignorée). Aucun réglage sur nos pages : imgsz 1024, conf 0,25, NMS par défaut, CPU.
Affectation : une ligne lue (lecture A, rôles P6e) reçoit la zone dont la boîte contient le centre de sa boîte de ligne (ALTO de la chaîne, appariement par texte) ; plusieurs zones → la plus petite ; aucune → zone inconnue.
Variantes (mesurées toutes deux, décision sur Y01a) :
- Y01a (découpe seulement) : régions de la lecture A, plus une coupure « + » quand deux lignes consécutives de même rôle tombent dans deux zones YOLO connues différentes.
- Y01b (YOLO seul) : régions = zones YOLO (coupure à chaque changement de zone connue), rôles de la lecture A.
Mesure gelée : `olr.mesure` (F1 « même région », rôle, ordre) par page.
Développement : 60 pages dev + écart (O07-O18, O23-O25) ; validation : O26-O28 (12, jamais utilisées pour Y01).
H-Y01 (adoption de Y01a) : sur dev+écart, nombre de pages à F1 = 1,00 en hausse ET aucune page en baisse de plus de 0,02 ; puis tenue sur O26-O28 (aucune page en baisse > 0,02).
Rapporté aussi : temps CPU par page ; pire page ; liste des pages changées.
