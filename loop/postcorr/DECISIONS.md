# Post-correction V0 — journal des décisions (daté)

## 01/10 — B0 : données
- Mandat : le mainteneur a demandé de lancer le protocole en autonomie (« vas y, … en autonomie ») ; cela vaut validation du plan de travail et du téléchargement (§12 du protocole).
- **Source retenue** : HIPE-OCRepair-Bench v0.9 (ICDAR 2026, github.com/hipe-eval/HIPE-OCRepair-2026-data, révision clonée le 01/10), partie **française** : `icdar2017` v1.1 (BnF, journaux XVIIe-XXe s., CC BY-NC-SA 4.0 ; train 391 unités / 952 k car., test 100 / 273 k) et `impresso-snippets` v1.0 (CC BY-NC-SA 4.0 ; 160 unités / 78 k car.). Usage recherche non commercial, conforme aux licences.
- Écartés : ICDAR 2019 FR1 (manuscrits HIMANIS, hors périmètre « imprimés »), FR3 (tickets de caisse), FR2 (IMPACT BnF, 209 k car., gardé en réserve comme second test hors distribution, CC BY-NC-SA 3.0) ; `overproof` (licence « research use only », anglais) ; allemand (`dta19`, `impresso-nzz`) hors périmètre V0 (langue), noté pour V1 (domaine BBVLM).
- **Découpage** : les splits HIPE réutilisent 21 identifiants de documents icdar2017 entre train et test (numérotation par split ou même document : invérifiable) → **re-découpage par groupe documentaire** sur l'ensemble train ∪ test ∪ dev : groupe = identifiant de document source (fr_periodical-N / fr_monograph-N ; document_id pour impresso) ; h = sha256(groupe) mod 10 : 0-1 test, 2 dev, 3-9 train. Les chiffres ne sont donc **pas** comparables au classement HIPE.
- **Unité** : les unités HIPE sont des paragraphes/chunks sans lignes (icdar2017) → V0 travaille sur des **pseudo-lignes** : la vérité terrain est coupée aux espaces en segments de 50-80 caractères, et le segment OCR correspondant est obtenu par l'alignement caractère (Levenshtein, rapidfuzz) de l'unité entière. Écart déclaré au §11.4 (« la ligne »).
- Filtrage (§3) : pseudo-lignes à rapport de longueur OCR/GT hors [0,5 ; 2] ou CER > 60 % écartées et comptées.

## 01/10 — B0 : statistiques produites, seuils figés (avant toute évaluation de système)
- Pseudo-lignes (50-80 car.) : train 12 945 (propre 6 571 / modéré 5 932 / lourd 442, 169 groupes), dev 1 064 (23 groupes), test 3 108 (propre 1 583 / modéré 1 410 / lourd 115 ; 49 groupes) ; 4 écartées (ratio/CER). Contrôle visuel de 9 alignements : corrects ; la vérité terrain contient elle-même des fautes (ex. « Party. Party. »), comme l'annonce le protocole.
- S0 (identité) sur test : CER propre 0,47 %, modéré 5,90 %, lourd 19,2 %, global 3,60 %.
- Contrat de sortie : `outils/contrat.py` ; test aller-retour source + éditions = cible sur tout train : OK.
- **Seuils figés** (repris du protocole, inchangés) : H1 (modéré) S2 ≥ 80 % de la réduction de CER de S3, latence ≥ 5× inférieure, taux de dégradation ≤ celui de S3 ; H2 (propre) S2 et S6 dégradation < 1 %, S3 et S5 au-dessus ; H3 (lourd) S4 réduction > S2 et dégradation ≤ S2 + 2 points ; H4 S6 domine chaque système en CER global, coût/ligne < S3. Verdicts sur test, IC 95 % bootstrap par groupe (1 000 tirages, graine 17).
- Puissance : strate lourde du test = 115 lignes / 20 groupes → H3 sera au mieux « non concluante » si les IC se chevauchent ; FR2 (ICDAR 2019) gardé comme second test hors distribution.
- Ressources : pas de GPU → S3/S4 (ByT5) entraînés sur CPU à petite échelle (ByT5-small, budget de pas déclaré) ou reportés ; S5 = sous-agents Claude sur échantillon stratifié.
