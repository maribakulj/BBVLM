# BBVLM — vérités terrain documentaires traçables

Version de travail locale fondée sur le dépôt `60b8ed3`. Elle ajoute un graphe
physique/logique, des propositions VLM par identifiant, des exports ALTO/METS
validés et une file de relecture. Les sorties automatiques restent des brouillons.

## Démarrage CPU

```bash
python -m pip install -r requirements-document.txt
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m bbvlm --help
```

Import d'un ALTO existant et export du paquet documentaire :

```bash
PYTHONPATH=src python -m bbvlm import out-pp/page.alto.xml /tmp/document.json
PYTHONPATH=src python -m bbvlm export /tmp/document.json /tmp/paquet --schemas schemas
```

Le paquet contient `document.json`, les ALTO par page, `mets.xml`, `review.json`
et `package.json`. Les mots non alignés ne reçoivent jamais de fausses coordonnées.

## Essai VLM réellement exécuté

Deux lectures de la même page historique ont été réalisées par les sous-agents
Terra et Luna, suivies d'une reprise sur quatre désaccords. Résultats et limites :
[experiments/terra_luna/README.md](experiments/terra_luna/README.md).

```bash
PYTHONPATH=src python scripts/evaluate_vlm_pilot.py
```

Cette commande rejoue les réponses conservées ; elle ne rappelle pas les modèles.

## Préparer une nouvelle lecture

```bash
PYTHONPATH=src python -m bbvlm prepare /tmp/document.json IMAGE.jpg P0001 /tmp/lecture
PYTHONPATH=src python -m bbvlm apply /tmp/document.json REPONSE.json /tmp/enrichi.json --model MODELE --request /tmp/lecture/request.json
PYTHONPATH=src python -m bbvlm export /tmp/enrichi.json /tmp/enrichi --schemas schemas
```

Ajouter `--show-ocr` à `prepare` pour tester la correction assistée par l'OCR ;
par défaut le texte du graphe n'est pas communiqué au lecteur.

## État de l'intégration

Voir [IMPLEMENTATION.md](IMPLEMENTATION.md) : changements, compatibilité avec
`produire.py`, cache/alignement PERO optionnel et limites non testées en conditions
réelles. Aucun modèle OCR n'est inclus. Les résultats historiques et anciens
protocoles restent dans [README-historical.md](README-historical.md), RAPPORT.md,
JOURNAL.md et state/, sans être requalifiés comme performances de cette version.

Licence du code : Apache-2.0. Attribution du corpus pilote dans son README.

## Boucle autonome dans cette sandbox

Le protocole et les critères sont dans `experiments/loop/protocol.json` ; l'état
reprenable est `experiments/loop/CHECKPOINT.json`. Les expériences ne certifient
jamais automatiquement des vérités terrain.

```bash
python3 scripts/autonomous_loop.py --execute
PYTHONPATH=src python3 -m bbvlm search DOSSIER/retrieval.sqlite 'Parlament'
```

Les phases CPU sont rejouables ; littérature, appels VLM réels et nouvelles
hypothèses restent pilotés par l'agent. Politique : Luna principal, Sol uniquement
sur risque explicite ; Terra disponible comme alternative, pas de triple lecture
systématique. Voir `experiments/loop/REFERENCE_AUDIT.md` : des erreurs dans les
annotations françaises distribuées empêchent actuellement de conclure à une
supériorité scientifique générale, malgré les gains géométriques mesurés.

Le pilote OLR A03 utilise des jetons visuels courts puis un binding logiciel vers
les IDs METS/ALTO. Il a supprimé l'erreur de recopie d'identifiants sur 42 régions,
mais pas les erreurs d'ordre/SSU/rôle ; voir le rapport
`experiments/loop/spiritualist-v1/olr-v2-validation/report.json`. Les deux pages
de validation testées sont consommées et ne seront pas réutilisées comme test
indépendant.

Pour les pages à colonnes simples, `bbvlm.order` propose maintenant un ordre
géométrique et ses arêtes sans appel VLM. Le test gelé 0014 obtient 378/378 paires
sur régions fournies ; il ne constitue pas encore une évaluation end-to-end.

L'essai A06 ajoute un groupement CPU par titres, parfait sur développement avec
rôles fournis, mais la validation 0029 échoue après une seule passe Luna
(rappel filtre 0,696 ; F1 SSU 0,680). Cinq désaccords viennent de publicités que
le modèle reconnaît éditorialement alors que la source les encode seulement en
`HEADER`/`TEXT`. La prochaine convention séparera donc rôle physique, genre et
flux ; 0029 ne sera pas rescored comme test indépendant.

A07 rend ce découplage exécutable. Sur 0039, il restaure parfaitement le flux
et l'ordre (21/21 régions, 210/210 paires), mais le F1 SSU reste à 0,591 car
Luna échange HEADER et TEXT. Une règle géométrique normalisée est maintenant
figée sur développement pour A08 ; 0039 est consommée.

Pour restaurer les poids et images omis d'un checkpoint portable :
`python3 scripts/restore_public_assets.py`, puis installer les dépendances
`requirements-document.txt` et `requirements-experiment.txt` dans un venv.

Le diagnostic A16 teste maintenant une réparation strictement additive des
boîtes CTC qui omettent une ponctuation terminale visible. Sur l'échantillon A15
déjà consommé, la capture sans filtre modifiait 179/184 mots et a été rejetée ;
le filtre par centroïde externe en modifiait encore 72/184. La proposition
prudente limitée à la ponctuation de bord ne change que quatre tokens, dont les
deux cadratins visiblement tronqués, sans nouveau chevauchement. Texte, IDs et
ALTO/METS restent invariants/valides. Cette sortie reste automatique jusqu'à une
validation géométrique nouvelle et indépendamment adjudiquée.

A17 renforce le paquet documentaire sans nouvelle inférence : le `structMap`
physique relie désormais chaque page à son image source et à son ALTO ; ALTO,
graphe et index portent taille et SHA-256, repris comme objets PREMIS 3. Le MODS
3.8 n'invente aucun titre/date : faute de notice sourcée, il expose seulement
l'identifiant local et la provenance automatique. METS core et PREMIS passent
leurs XSD hors ligne ; le XSD MODS officiel reste explicitement non validé car
son téléchargement amont répond 403.

A18/A19 reviennent aux références et au coût : quatre nouveaux ouvrages OCR-D/SBB
sont téléchargés et audités au mot, quatre autres réservés non ouverts. Une voie
géométrique sans réseau OCR est mesurée sur 94 lignes ; elle produit de bons
accords moyens mais laisse passer neuf mauvaises boîtes, donc reste expérimentale.
La cible est désormais explicitement une lecture VLM partagée texte/relations/
preuves et un alignement CTC payé uniquement si nécessaire, pas un PERO complet
surmonté d'un VLM. Hypothèses et ablations :
[ARCHITECTURE_A19.md](experiments/loop/ARCHITECTURE_A19.md).

A30 teste enfin l'OCR VLM sur 16 régions françaises inédites d'une transcription
manuelle BnF, en crops polygonaux haute résolution et IDs opaques. Luna obtient
1,7310 % de CER NFC strict ; l'escalade Sol aveugle post-hoc 1,4647 %. Une vue
retrieval documentée descend à 0,8440 % et 0,5739 % après harmonisation des
tirets/césures, mais aucune sortie n'atteint 0 %. La référence elle-même contient
au moins un U+FFFD et des lectures à adjuger ; originaux, candidats et rapports
restent séparés dans `experiments/loop/bnf-region-ocr-a30/`.
