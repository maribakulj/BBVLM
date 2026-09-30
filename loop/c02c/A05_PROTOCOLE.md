# A05 — révision « blancs seuls » d'un verdict adjugé (pré-enregistré, 30/09, avant mesure)

Contexte : R3/R4 (blanc avant « ( », blanc après point d'abréviation collé) rejetées au critère figé
à cause d'un seul verdict adjugé antérieur à P6d (hackherz l006 « 2.Cor.XII.3.4 »). A02 : les deux
relecteurs aveugles écrivent « 2. Cor. XII. 3. 4 » ; VT « 2. Cor. XII 3. 4. ». A01 (accord glyphe à
glyphe avec la VT) non remplie, mais les deux relecteurs ont la segmentation en mots de la VT (5 mots).
A04 (22 lignes, 2 relecteurs aveugles) confirme la même convention sur 3 autres lignes
(DasWeL « vff. xxxviij. jar », « Vff. xiij. jar », buchdas « lengſt (darumb »).

Règle A05 : quand les deux relecteurs aveugles ont la même segmentation en mots que la VT distribuée
(mêmes positions de blancs, glyphes ignorés) et que le verdict adjugé s'en écarte seulement par des
blancs, les BLANCS du verdict sont remplacés par ceux de la VT ; ses glyphes sont conservés.
Application : on retire les blancs du verdict et on y reporte ceux de la VT, par alignement des
glyphes sans blanc (un blanc suit la ponctuation non appariée collée au glyphe apparié) :
hackherz l006 « 2.Cor.XII.3.4 » → « 2. Cor. XII. 3. 4 » (identique aux deux relecteurs A02).
Implémentation : outils/bilan_adj.py reblanc(), fichier adj/blancs.json (ids), BBVLM_A05=1.

Critère ensuite : R3/R4 réévaluées au critère figé habituel (texte adjugé non en hausse, aucune page
+1, CRITERE non en recul).
