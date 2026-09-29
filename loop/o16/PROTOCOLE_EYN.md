# EY1 — Eynollah pour les lignes manquées par kraken — figé avant mesure, 2026-09-29

Pages : celles où des lignes de la VT restent sans ligne kraken (IoU ≥ 0,5)
après S08/S02 : durrgeda (3), 852691769 (10), eberbrev (1), extraudeu (1),
herbdulc (1), erasexom (1). Témoins sans manque : erobdefoa, chiamerk.
Méthode : eynollah (modèles v0.3.1, lignes seulement) ; ses lignes qui ne
recouvrent aucune ligne kraken (IoU < 0,3 et recouvrement < 50 %) sont
ajoutées aux candidates. Mesures : lignes VT trouvées, précision des lignes,
ALTO texte+IoU80 (avec ancrage S05). Adoption : gain sur les pages à manque,
aucun recul sur les témoins.
