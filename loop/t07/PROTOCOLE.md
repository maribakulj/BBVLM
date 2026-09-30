# T07 — espaces repris d'une relecture AVEUGLE ligne par ligne (pré-enregistré 30/09 20h20, pilote)

Constat : T06 (lecture montrée) échoue par ancrage ; en aveugle (A04), deux relecteurs retrouvent la segmentation de la VT sur les lignes où nous nous trompions.
Méthode : vignette de chaque ligne (TextLine de l'ALTO courant), agrandie ; deux relecteurs Opus aveugles (sans notre lecture) transcrivent chaque ligne ; pour chaque ligne, si les deux relecteurs ont la même segmentation (même suite de mots une fois les blancs retirés alignés sur nos glyphes), nos blancs sont remplacés par les leurs (reblanc : nos glyphes gardés) ; sinon inchangé.
Pilote : 4 pages de développement portant des soudures connues : hackherz/24, DasWeL/71, baltdiss/24, buchdas/24 (aucune page de l'écart).
Critères : texte glyphe (adjugée) par page non en hausse et total en baisse ; CRITERE des 4 pages non en recul. Si le pilote passe : essai sur toutes les pages dev, puis écart rapporté.

## T07c — validation (pré-enregistrée 30/09 20h40)
Pages : parmi les pages de développement (O07-O18) hors pilote, une sur six dans l'ordre alphabétique des dossiers (8 pages). Même procédure (2 relecteurs aveugles, report T07c). Critères : texte glyphe total en baisse et aucune page en hausse ; CRITERE des 8 pages non en recul. Adoption si tenus (coût : 2 passes VLM de plus par page, à discuter en mode économe).
