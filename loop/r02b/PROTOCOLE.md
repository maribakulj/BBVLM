# R02b — recherche mesurée contre la référence adjugée auditée (changement de mesure, pré-enregistré)

Figé le 2026-09-30 (~21h10 Paris) avant calcul.

Constat : parmi les occurrences manquées de la recherche (60 pages, ALTO sr4), 181 sur 262 pertes « texte » ont un terme indexé différent au même endroit, dont de nombreuses fautes de la VT distribuée (« sindet » pour « findet », « fatis » pour « satis », « fiir » pour « für »). Le texte est déjà mesuré contre la référence adjugée auditée (règle A2 + A01) ; la recherche ne l'est pas.
Changement : mêmes boîtes de mots (PAGE VT) ; le texte de chaque mot est pris dans la ligne adjugée auditée (bilan_adj.reference_adjugee) quand elle a le même nombre de mots que la ligne PAGE, sinon celui de la VT (inchangé). Même règle d'appariement (terme en vue recherche, IoU ≥ 0,5).
Rapporté : rappel médian, pages ≥ 0,95, pires pages, avec la mesure R01 à côté (jamais remplacée sans être rapportée). Ce n'est pas un gain de la chaîne : c'est le retrait d'un artefact de la référence.
