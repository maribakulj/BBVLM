# A33 — rattachement CPU guidé par la ponctuation transcrite

Gelé le 2026-09-27 avant calcul des scores A33. Les huit pages A28 sont du
développement consommé. A32 perd visuellement le point de `M***.`, la virgule
de `fertile,` et le point de `1725.`. Hypothèse : quand le token déjà transcrit
annonce une ponctuation de bord, récupérer au plus une petite composante Otsu
écartée, située entre la boîte filtrée et l'étendue CTC de ce token.

Deux ablations fixes : signes finaux seulement; signes initiaux et finaux.
Base inchangée : composantes corps + satellites A32. Petite composante : aire
entre 2 pixels et 0,08 × hauteur². Son écart horizontal au corps doit être au
plus 0,40 × hauteur; son centre doit rester dans l'étendue CTC avec une marge
de 0,15 × hauteur et entre bande-corps−0,20 × hauteur et bande-corps+0,45 ×
hauteur. Prendre la plus proche, au plus une par bord. Aucun seuil ne sera
modifié après score.

Ensembles inspirés mais non copiés comme algorithme de Tesseract : début
`('`\"«‹[{—–-`; fin `).,;:?!…'`\"»›]}—–-*`. Le code Tesseract courant expose
des ensembles de ponctuation initiale/finale et traite les petits contours par
réassignation conditionnelle; A33 n'utilise ni son classifieur ni ses scores.

Le constructeur voit image, rectangle de ligne, boîtes CTC existantes et texte
de token; jamais les boîtes de référence. Ici le texte/tokenisation et les
rectangles de ligne sont oracle, l'alignement CTC est en cache et la baseline
est synthétique : pas de revendication end-to-end. Mesurer IoU, IoU50/80,
améliorations/régressions appariées, signes sauvés, coût et résultats par page.
Inspecter toutes les boîtes modifiées sur pixels sans overlay. Aucun gate final
ne peut passer; originaux et vérité terrain restent immuables.

Amendement avant tout rapport complet et avant lecture de score : le fixture
synthétique initial mettait son point à l'intérieur du rayon A32; il ne pouvait
donc pas tester A33. Le point est déplacé entre les rayons A32 (0,30 h) et A33
(0,40 h), sans changer l'algorithme ni ses seuils. Conversion explicite des
coordonnées OpenCV en entiers Python après refus de sérialisation. Le premier
lancement s'est interrompu avant `report.json`; le seal partiel et l'image
provisoire sont conservés dans `pretest-fixture-run/`.

Deuxième correction du fixture avant lecture des résultats : la projection
plaçait encore le point dans la bande dense A32, qui le conservait par règle.
Il est déplacé sous cette bande tout en restant dans la fenêtre verticale A33.
Le lancement concurrent a pu finir; ses sorties non inspectées sont préservées
dans `pretest-fixture-run-2/`. Aucun seuil ni octet du corpus n'a changé.
