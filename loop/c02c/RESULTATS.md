# A04 / C02c — résultats (30/09)

Audit aveugle A04 : 22 lignes où notre lecture a un nombre de mots ≠ VT ; 2 relecteurs Opus sans candidats (relecteur1.json, relecteur2.json, meta.json).

| issue | lignes |
|---|---|
| les deux relecteurs = notre compte ≠ VT → **exclues (C02c)** | 7 : hackherz « eſt quod proficeret… », herrkurt « Numer. 3. cap. v. 50… », extraudeu « L.S. », emmeprac « l. 1. in prin ff. … », « in iudicio defert… », erasexom « hinc ſibi tribuat… », caladr « Vincla pedi… » |
| les deux relecteurs = VT → **nos erreurs** | 13 : DasWeL « vff.xxxviij.jar », « Vff.xiij.jar » ; hackherz « ihmviel » ; 852691769 « … eſt u- » ; extraudeu « Krieges⸗und » ; AyrmThes « haud male… » (+1 mot), « ſtat fuiſſe… » (−1) ; buchdas « tent die vieer… », « lengſt(darumb » ; 688357687 « Bk. Achter Th. » (signature « (F) » omise ?) ; hermhyst ligne fusionnée ; AphoqvSuS « VerboDEI » |
| relecteurs en désaccord | 2 : brochrnx « nimmt⸗ du » (×2), buchdas « vff kommen » |

CRITERE (référence reproductible, cache W05, MODE=chaine2) : **35 → 39 / 60** (etat_c02c/).
- O07-O17 25 → 28/44 : herrkurt ✓, emmeprac ✓, erasexom ✓ ; hackherz 4 → 3 lignes en échec, extraudeu 2 → 1 (toujours ✗).
- O23 2 → 3/4 : caladr ✓. O18 3/4, O24 3/4, O25 2/4 inchangés.
- Aucune autre page modifiée (déterminisme vérifié ligne à ligne contre etat_1525/).

Nos erreurs → pistes : 4 soudures sur blancs d'abréviation/parenthèse (R3/R4, cf. A05), 2 soudures de mots (« ihmviel », « VerboDEI »), 1 fusion de lignes (hermhyst, segmentation).

## A05 + R3/R4 (30/09 15h50)
- A05 (c02c/A05_PROTOCOLE.md, pré-enregistrée) appliquée à hackherz l006 : verdict « 2.Cor.XII.3.4 » → « 2. Cor. XII. 3. 4 » (= les deux relecteurs aveugles A02). Seul verdict révisé (c02c/a05/blancs.json ; dans le dossier de page : adj/blancs.json).
- R3/R4 réévaluées sous A05 au critère figé : texte adjugé (4 pages modifiées) glyphe 60 → **54**, norm 57 → 51, aucune page en hausse (hackherz 8 → 4, extraudeu 2 → 1, buchdas/24 40 → 39, DasWeL 10 → 10).
- CRITERE 39 → **40/60** (etat_a05/) : buchdas/24 ✓ ; DasWeL 3 → 1 ligne en échec, hackherz 3 → 2 ; extraudeu « L.S. » → « L. S. » (= VT, ligne jugée au lieu d'être exclue) ; aucune page en recul, petits lots identiques.
- **R3/R4 adoptées** (défaut BBVLM_R3=BBVLM_R4=1 dans p2.parenthese) ; A05 défaut BBVLM_A05=1.
