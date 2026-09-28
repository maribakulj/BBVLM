# A83 — mesurer PERO sans payer son OCR

Les seuls étages layout/crop ont réellement tourné sur les4pages A80 consommées.
RUN_OCR=no et RUN_DECODER=no ; assertions `parser.ocr is None`, `decoder is None`,
aucun texte/logit sur toutes les lignes. Les imports de modules OCR ne chargent
pas un reconnaisseur. Le poids ParseNet CPU seul est chargé.

Coût batch : chargement0,242s, layout25,565s, recadrage3,889s, remappage de six
exemples0,014s ; script entier31,303s hors imports/restauration. Six forwards
ParseNet mesurés par interception de get_maps, à cause de l'adaptation de résolution,
pas seulement quatre passes supposées. Quatre threads, ordre des pages fixé.
La chaîne A80 dense+YOLO prenait120,639s pour ses deux scripts (dont scoring et
écritures) ; ses96forwards et les six PERO sont des réseaux/tailles différents,
pas des unités de coût interchangeables. Le téléchargement de363408419octets et
l'installation initiale sont séparés des temps d'inférence ; ils ne sont pas gratuits.

| Page | A80 précision/rappelIoU50 % | PERO layout précision/rappelIoU50 % |
|---|---:|---:|
| Reichs_Post_Reuter_1700-11-16_0004 | 74.19/100.00 | 93.88/100.00 |
| Holzmindisches_Wochenblatt_1785-07-30_0006 | 47.62/100.00 | 96.67/96.67 |
| Koelnische_Zeitung_1866-06_1866-09_0539 | 90.89/94.91 | 84.67/98.47 |
| Koelnische_Zeitung_1924_0018 | 98.30/93.95 | 98.95/97.64 |

PERO émet1433lignes,1317appariementsIoU50 pour1343références ; A80 émettait1388
propositions et1272appariements. Le compromis varie : PERO retrouve plus de lignes
sur1866 mais sa précision y est inférieure. Pas de supériorité uniforme du candidat,
pas de géométrie de mots, aucun OCR ou OLR nouvellement évalué.

Sur la ligne inclinée A81, support source du crop PERO : encre voisine45,14 %→0,175 %,
rappel de l'encre du polygone assigné100 %→99,42 %. Le crop a été réellement inspecté
et la ligne est remise à plat. Mais les deux dernières cibles gagnent en couverture
ET en contamination (1866:22→76pixels voisins ;1924:270→798). Ne pas promouvoir
PERO crop comme parfait. Mesure sur Otsu pleine page/PAGE : différente de l'Otsu
localA81/A82, scores non interchangeables. Les dénominateurs sont conservés.

Provenance : fichiers/modèle/config/images hachés, prédictions scellées avant XML ;
association des six lignes par IoU entre boîtes PRÉDITES, sans texteGT. Origine de
l'échantillon A81 oracle et consommée explicitée. Aucun gate global,100Test intacts.
Suite A84 : lecture aveugle sur crops PERO rectifiés en préservant leur échelle
native ; mesurer OCR/coût de rendu sans relancer détection/reconnaissance PERO.
