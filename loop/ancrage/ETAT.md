# Chantier ANCRAGE + POST-CORRECTION — état (lire d'abord)

Demande du mainteneur (01/10) : mettre en œuvre en autonomie `ancrage/PLAN.md` (+ `ancrage/protocol.yaml`) et `postcorr/PROTOCOLE.md`, jusqu'à atteinte des objectifs ou gate négatif. Avis initial consigné dans JOURNAL (01/10).

## Contraintes d'environnement
- CPU seul (4 cœurs, 15 Go RAM), disque ≈ 7 Go libres ; pas de GPU (jeton KAGGLE_USERNAME/KAGGLE_KEY ou MODAL_TOKEN_ID/SECRET absent). HF accessible (01/10), GitHub releases 403, Zenodo partiel.
- Écart déclaré au plan : volumes réduits pour le CPU (Phase A uniquement : backbone gelé, sonde légère, caractéristiques en cache). Toute conclusion porte la mention « échelle CPU ».
- Les 0 % de BBVLM restent « contre référence adjugée Opus » ; boîtes de référence = OCR-D GT niveau 2 (Word Coords).

## Objectifs et gates — chantier A (ancrage), dans l'ordre
| étape | contenu | gate / critère | état |
|---|---|---|---|
| A0 ✓ | contrat d'expérience : occurrence = (version texte, début, fin, id) ; convention boîte = enveloppe d'encre OCR-D Word ; ponctuation selon VT ; partitions par œuvre (dev = œuvres des pages O07-O25 ; test = œuvres jamais lues par la boucle) ; marges fixées | contrat gelé, `protocol.yaml` required_before_freeze rempli | **fait 01/10** : ancrage/CONTRAT.md v1 ; L55 (têtes de localisation) → bras G1a |
| A1 ✓ | 64 blocs traçables (3-8 lignes) tirés de pages OCR-D : pixels, texte diplomatique, offsets, boîtes, transformation crop→page ; tests aller-retour | tests passent | **fait 01/10** : 1 944 blocs (train 1 495 / 45 œuvres ; dev 271 / 12 ; test 178 / 9 œuvres, 858 lignes, 6 059 mots — sous la cible de 400 blocs, écart déclaré), 75 606 occurrences, test_a1 0 erreur ; debug64 (45 œuvres, 56 avec mots répétés) ; ancrage/a1/ |
| E0 ✓ | Qwen3-VL-2B (révision 89644892) sur CPU : trace tokens↔offsets, mapping patch→page exact, parité native avec/ sans instrumentation, coût | 0 erreur d'indexation inexpliquée | **fait** : grille exacte (6e-8), trace exacte 23/23, parité 0,0 |
| E1 ✗ | sonde G1 (états seuls) / G2 (états + carte fine) contre G0 (W05+W06 actuel) sur œuvres de test, transcription fournie | G2 > G1 hors entraînement, et comparaison à G0 au CRITERE (le go vers la suite exige G2 ≥ G0 ou un gain d'économie démontré) | **non-go (02/10)** : G0 7/9 œuvres, iou 0,898 ; G1a 0/9 (0,221) ; G1 0/9 (0,303) ; G2 0/9 (0,316) ; H1 et H2 non tenues — ancrage/E1_RESULTATS.md |
| E2 — | contrôles : image fausse, carte permutée, neutralisée, translation/échelle, mots répétés | la géométrie suit les transformations | sans objet (non-go E1) |
| E3-E6 | couplage lecture, abstention, blocs sans lignes, révision atomique | GPU requis pour E3 (entraînement conjoint) → arrêt motivé et rapport si pas de jeton | — |

## Objectifs et gates — chantier B (post-correction V0), en parallèle des calculs longs
| phase | contenu | gate | état |
|---|---|---|---|
| B0 ✓ | données (ICDAR 2017/2019 post-OCR FR, licences vérifiées), alignement, strates, S0, tests ; seuils H1-H4 figés dans postcorr/DECISIONS.md | statistiques produites, seuils figés | **fait 01/10** : HIPE-OCRepair FR (icdar2017 + impresso-snippets), re-découpage par groupe (fuite possible dans les splits HIPE), pseudo-lignes 50-80 car. ; test 3 108 lignes / 49 groupes (lourd 115) ; S0 test CER 3,60 % ; contrat + test aller-retour OK ; postcorr/DECISIONS.md |
| B1 ✓ | S1 canal bruité (CPU), S5 LLM sur échantillon (sous-agents Claude) | chiffres reproductibles par une commande | **fait 01/10** : S1 test −2,9 % CER, 0,4 % propres dégradées ; S5 (Sonnet, 150 lignes) −55 % modéré / −43 % lourd mais 18 % de propres dégradées |
| B2 ✓ | S2 étiqueteur, S3 ByT5 (CPU si faisable à petite échelle, sinon GPU) | go/no-go H1/H2 | **fait** : H1 infirmée (S2 = 35 % du gain de S3), H2 confirmée (S2/S6 0,13 % de propres dégradées) |
| B3-B4 ✓ | S4, S6, rapport | verdicts H1-H4 | **fait 02/10** : H3 infirmée (S4 dégrade 19 % des lourdes), H4 infirmée (S6 −13,1 % < S4 −23,6 %) ; postcorr/RAPPORT.md |

## Prochaine étape
- **Les deux chantiers sont terminés** (02/10) : ancrage arrêté au gate E1 (non-go à l'échelle CPU) ; post-correction menée jusqu'au rapport (H1 infirmée, H2 confirmée, H3 et H4 infirmées). Tout ce qui reste exige un GPU (LoRA/entraînement conjoint pour l'ancrage ; ByT5-base, n-best, bruit synthétique pour la post-correction) ou une décision du mainteneur (contrainte anti-normalisation des césures pour S3/S4 ; seconde série de sondes E1 sur train complet).

## Prochaine étape (avant le 02/10)
- Chantier A **arrêté** au gate E1 (non-go à l'échelle CPU) ; reprise possible seulement avec GPU (LoRA, sonde initialisée par les têtes de localisation, prédiction de frontières).
- Chantier B : reprendre S2 (époque 3), régler le seuil sur dev, test ; puis S3 (ByT5-small) si faisable sur CPU.

## Ancienne prochaine étape
E0 : instrumentation Qwen3-VL-2B (venvq, révision 89644892, téléchargée) sur debug64 ; B0 en parallèle.

## Environnement
- venvk : chaîne BBVLM (kraken, safetensors 0.7) ; venvq : Qwen/transformers 5.18 (torch partagé via .pth). venvc (Calamari) supprimé le 01/10 pour la place disque (W05 couvre toutes les pages ; sorties Calamari en cache) ; w05cache supprimé (régénérable).
