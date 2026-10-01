# Chantier ANCRAGE + POST-CORRECTION — état (lire d'abord)

Demande du mainteneur (01/10) : mettre en œuvre en autonomie `ancrage/PLAN.md` (+ `ancrage/protocol.yaml`) et `postcorr/PROTOCOLE.md`, jusqu'à atteinte des objectifs ou gate négatif. Avis initial consigné dans JOURNAL (01/10).

## Contraintes d'environnement
- CPU seul (4 cœurs, 15 Go RAM), disque ≈ 7 Go libres ; pas de GPU (jeton KAGGLE_USERNAME/KAGGLE_KEY ou MODAL_TOKEN_ID/SECRET absent). HF accessible (01/10), GitHub releases 403, Zenodo partiel.
- Écart déclaré au plan : volumes réduits pour le CPU (Phase A uniquement : backbone gelé, sonde légère, caractéristiques en cache). Toute conclusion porte la mention « échelle CPU ».
- Les 0 % de BBVLM restent « contre référence adjugée Opus » ; boîtes de référence = OCR-D GT niveau 2 (Word Coords).

## Objectifs et gates — chantier A (ancrage), dans l'ordre
| étape | contenu | gate / critère | état |
|---|---|---|---|
| A0 | contrat d'expérience : occurrence = (version texte, début, fin, id) ; convention boîte = enveloppe d'encre OCR-D Word ; ponctuation selon VT ; partitions par œuvre (dev = œuvres des pages O07-O25 ; test = œuvres jamais lues par la boucle) ; marges fixées | contrat gelé, `protocol.yaml` required_before_freeze rempli | à faire |
| A1 | 64 blocs traçables (3-8 lignes) tirés de pages OCR-D : pixels, texte diplomatique, offsets, boîtes, transformation crop→page ; tests aller-retour | tests passent | à faire |
| E0 | Qwen3-VL-2B (révision 89644892) sur CPU : trace tokens↔offsets, mapping patch→page exact, parité native avec/ sans instrumentation, coût | 0 erreur d'indexation inexpliquée | à faire |
| E1 | sonde G1 (états seuls) / G2 (états + carte fine) contre G0 (W05+W06 actuel) sur œuvres de test, transcription fournie | G2 > G1 hors entraînement, et comparaison à G0 au CRITERE (le go vers la suite exige G2 ≥ G0 ou un gain d'économie démontré) | à faire |
| E2 | contrôles : image fausse, carte permutée, neutralisée, translation/échelle, mots répétés | la géométrie suit les transformations | à faire |
| E3-E6 | couplage lecture, abstention, blocs sans lignes, révision atomique | GPU requis pour E3 (entraînement conjoint) → arrêt motivé et rapport si pas de jeton | — |

## Objectifs et gates — chantier B (post-correction V0), en parallèle des calculs longs
| phase | contenu | gate | état |
|---|---|---|---|
| B0 | données (ICDAR 2017/2019 post-OCR FR, licences vérifiées), alignement, strates, S0, tests ; seuils H1-H4 figés dans postcorr/DECISIONS.md | statistiques produites, seuils figés | à faire |
| B1 | S1 canal bruité (CPU), S5 LLM sur échantillon (sous-agents Claude) | chiffres reproductibles par une commande | à faire |
| B2 | S2 étiqueteur, S3 ByT5 (CPU si faisable à petite échelle, sinon GPU) | go/no-go H1/H2 | — |
| B3-B4 | S4, S6, rapport | verdicts H1-H4 | — |

## Prochaine étape
A0 + téléchargement Qwen3-VL-2B (révision épinglée) en fond ; B0 recherche des données en parallèle.
