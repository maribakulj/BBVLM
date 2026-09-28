# Veille sur la branche d'astra

| date | tête vue | nouveautés | conséquence pour nous |
|---|---|---|---|
| 2026-09-28 08:10 | c5f7c94 (A35) | aucune depuis l'analyse initiale | A32 (filtre composantes) passe CRITERE sur A28/A34 : candidat à réutiliser pour l'étage boîtes |
| 2026-09-28 10:15 | 71ac3e3 (A36-A51) | **A37** : lignes prédites PERO + A32 + routeur « pas d'expansion verticale », 4 pages SBB neuves : IoU mot moyen 0,568→0,854, rappel IoU80 0,5 %→68,6 %, 0 passe VLM, 10,6 s CPU/4 pages. A38-A44 : gardes rejetées. **A46** BnL fr : PERO CER 0,22 %, 9/12 blocs exacts. **A48-A49** Finlam (presse) : colonnes par modes récurrents du bord gauche, ordre global 0,67→0,88, F1 paires d'articles 0,20→0,66 (validé sur 6 pages neuves). A50-A51 frontières d'articles par VLM : rejetées (F1 0,488→0,482). A audité notre O01. | (1) étage boîtes : A37 est la référence à battre, à noter avec CRITERE.md et contre `connexe` ; lignes PERO utilisables pour la segmentation. (2) OLR : son ordonnanceur de colonnes est un acquis à reprendre plutôt qu'à réinventer. (3) Son constat « payer le VLM pour la sémantique, pas pour les coordonnées » rejoint le nôtre. (4) Il n'a pas de mesure OCR pleine page à 0 % : notre étage texte est en avance. |
| 2026-09-28 11:10 | 19ed72d (A52) | Rejoue nos vues O02 (borrdisc 19, drabnota) avec Luna puis Sol. Romain : Luna 0 % en vue « retrieval » (sans accents) mais 0,27 % diplo (modernise préferent→préfèrent) ; Opus 0 %. Fraktur : Luna 4,8 %, Luna+Sol 1,9 %, **Opus 1,3 %** (vue retrieval). Conclusion d'astra : l'écart est la résistance du modèle à la modernisation, pas la résolution ; Opus reste le meilleur lecteur diplomatique. Signale que la réclame de drabnota se lit « werck » alors que notre référence adjugée dit « wort ». Rappelle que nos adjudications sont faites par des modèles, pas par des humains. | (1) Confirme le choix d'Opus comme lecteur. (2) Point « werck » : revérifié à l'aveugle (voir JOURNAL). (3) Critique juste : l'adjudication par modèle n'est pas une vérité humaine ; nos 0 % valent « 0 faute contre une référence corrigée par deux arbitres Opus concordants ». À dire dans chaque résultat. |

## f3b5a84 / bd332a1 — astra A53 (vu le 2026-09-28, après O10)

A53 : arbitrage VLM (Luna) de 15 désaccords VLM/PERO-CTC en cache. CER agrégé
meilleur (2,76 → 1,47 % en vue recherche) mais **porte de non-régression
ratée** : 3 lignes exactes cassées, dont deux omissions lexicales « certaines »
(t perdu dans verſtehen, ſextodecimo). Décision astra : CTC = signal de
contradiction, pas de réécriture automatique.
*Conséquences ici* : même constat que notre règle A2 (un arbitre seul renverse
à tort : ﬂ → ſl sur herrkurt) — convergence indépendante. Notre P3 réécrit une
ligne par un seul arbitre : risque identique, mesuré sans régression jusqu'ici
(O07-O10), mais à protéger : P3 ne devrait remplacer une ligne où A et B
concordent jamais (déjà le cas : seules les lignes en désaccord sont
arbitrées). Idée à reprendre : porte de non-régression par ligne gelée avant
données neuves. PERO toujours inaccessible ici (modèle bloqué).

## aa29cec / 562f31a / 2e3c0d7 — astra A54-A56 (vu le 2026-09-28, pendant O12)

- **A54** (16 blocs BnL neufs, presse) : PERO + routeur A37 + une passe VLM
  (image + candidat PERO) + garde mécanique (refus des réécritures non
  traçables) : CER recherche 0,93 → 0,68 %, portes de non-régression passées ;
  4/16 blocs exacts. Boîtes : IoU80 au mot 33,5 % (15,8 % en français).
- **A55** : boîtes BnL = conventions mixtes (enveloppes CTC du fournisseur) ;
  garde de largeur rejetée ; les rectangles BnL ne sont pas une vérité au mot.
- **A56** : Europeana Newspapers (Zenodo 2583866) = régions + ordre seulement,
  0 TextLine, 0 Word → rejeté comme vérité de boîtes, utile pour l'OLR presse.
- Astra audite notre O11/S03.
*Conséquences ici* : (1) notre texte est à un autre ordre de grandeur sur les
livres SBB (plusieurs pages à 0 contre 4/16 blocs exacts), mais astra mesure la
presse, que nous n'avons pas (bloquée) ; (2) sa garde « réécriture traçable »
rejoint notre A2 et notre consigne P3 ; (3) son constat « vérité au mot non
fiable » vaut aussi pour nous : les VT SBB OCR-D ont des mots manuels
(polygones), c'est pourquoi nous restons sur SBB pour les boîtes ; (4) OLR
presse : Europeana (régions + ordre) est un banc accessible via Zenodo côté
astra — Zenodo bloqué ici.

## f70b292 … 996f30e — astra A57-A83 (vu le 2026-09-28, après O12)

27 commits, orientés **segmentation de presse** : Chronicling Germany (801
références auditées, réserve de test gelée), détecteurs YOLO de régions et
**Eynollah** (étage lignes dense : 98,3 % des pixels du masque dans les
polygones de ligne, 84 % de l'union couverte, A74), fusion de lignes
contrainte par région validée sur 4 pages neuves (A80 : +1 correspondance,
aucune perte ; précision 47-98 % selon le journal). A81-A83 : contamination
des recadrages par les lignes voisines, masquage par contour rejeté (A82),
étapes PERO mesurées sans reconnaissance (A83). File d'expériences
reprenable (A62).
*Conséquences ici* : (1) astra traite la presse, nous les livres ; nos
chiffres ne se comparent pas directement. (2) Même diagnostic que notre O10
(heptaldai) et notre B01 : l'encre des lignes voisines pollue recadrages et
boîtes. (3) Eynollah (segmentation de mises en page complexes) pourrait
couvrir nos trous kraken (titres d'apparat durrgeda, S06 non intégré) — à
évaluer si ses modèles sont accessibles ici. (4) Sa discipline (réserve de
test gelée, gates figés) rejoint nos protocoles O10-O12.
Accès vérifié : paquet `eynollah` 0.9.2 sur PyPI ; modèles v0.3.1 (1,9 Go)
téléchargeables depuis la release GitHub qurator-spk/eynollah (Zenodo et HF
bloqués ici). Non intégré : TensorFlow + ancienne version des modèles, pour un
trou rare chez nous (titres d'apparat) ; à reprendre si les livres testés
montrent plus de lignes non trouvées.
