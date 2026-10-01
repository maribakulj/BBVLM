# BBVLM : plan développé pour une lecture et une localisation conjointes

**Document de conception, version 1.0 du 1er octobre 2026.**

Ce document propose un programme expérimental. Il ne décrit pas un modèle déjà entraîné ni une amélioration déjà mesurée. Aucun changement de dépôt, lancement d'entraînement ou achat de calcul n'est inclus dans sa rédaction. Les dimensions, volumes de données, durées et seuils nouveaux sont des propositions à approuver avant gel.

## 1. Décision de projet

Conserver BBVLM comme projet principal et y isoler un nouveau noyau appris. Ne pas réécrire son graphe documentaire, ses exports ou sa provenance pour commencer. Ne pas transformer Hans et Saknussemm en dépendances neuronales. Conserver leurs tests, observations et références expérimentales. Ne pas ajouter Kraken, PERO et un VLM supplémentaire au chemin normal du candidat.

Le problème étudié est la réutilisation de la perception visuelle et des états du lecteur pour attribuer le texte à ses occurrences spatiales. Le premier démonstrateur travaille sur de petits blocs d'imprimé patrimonial. Il ne prétend pas encore traiter universellement toute une bibliothèque.

L'unification se mesure à trois niveaux :

1. **Calcul partagé** : pas de seconde reconnaissance indépendante pour obtenir les boîtes.
2. **Identités partagées** : une occurrence textuelle et son support spatial ne sont pas deux listes réconciliées approximativement après coup.
3. **Apprentissage couplé** : l'accès spatial peut améliorer la lecture, au lieu de dessiner seulement une boîte après une transcription déjà achevée.

Un seul checkpoint n'implique ni une seule opération GPU ni une seule fenêtre d'image. Les encodages de tuiles, les reprises et les passages du décodeur doivent être comptés.

### Résultat minimum recherché

Sur un bloc de trois à huit lignes, produire une transcription diplomatique et des occurrences localisées. Supporter les mots répétés, la ponctuation de bord, les espaces atypiques et les lignes voisines. Réussir sans utiliser les boîtes de référence à l'inférence. Garder les éléments non résolus visibles dans un paquet de propositions. Mesurer la qualité sur des documents absents de l'entraînement.

### Hors périmètre du premier cycle

Ne pas développer simultanément manuscrits, tables imbriquées, NER, résumés, identification d'articles, nouveau serveur, nouvel éditeur ou distillation vers plusieurs formats. La structure éditoriale reste une destination du modèle documentaire, pas une tâche supplémentaire du premier entraînement.

## 2. Ce que la littérature apporte effectivement

### ViTLP : occurrence et localisation dans le même flux

ViTLP représente chaque mot avec ses sous-tokens et un marqueur de localisation. Un petit décodeur local produit les coordonnées à partir de l'état associé. C'est un précédent direct pour un lecteur qui conserve l'identité mot-boîte, tout en évitant de faire traverser quatre coordonnées séparées à tout le gros décodeur. La méthode n'est pas une certification de boîtes patrimoniales. [R1]

### DeepSolo++ : une même représentation porte texte et géométrie

DeepSolo++ exploite des points ordonnés et un décodeur commun pour reconnaître et localiser le texte. La supervision CTC y est un mécanisme d'apprentissage, pas un moteur OCR externe à ajouter. Le domaine est le texte de scène : la transférabilité aux pages historiques doit être testée. [R2]

### PILOT : conserver ouverte la représentation de sortie

PILOT compare une sortie discrète à une variante continue dans un cadre documentaire. Le résultat ne permet pas de décréter qu'une tête de régression est toujours supérieure. La supervision et les évaluations sont largement harmonisées à la ligne ; elles ne remplacent pas une étude des frontières de mots. [R3]

### SCVER : le détail visuel peut influencer le décodage

SCVER permet au décodeur de consulter des caractéristiques antérieures à leur compression en fonction de son état courant. L'article décrit aussi un apprentissage spatial instable sans guidage. Le point utile est la consultation avant la décision textuelle. Ses points de consultation ne doivent pas être pris directement pour des boîtes ni pour des preuves causales. Référence récente, résultats non reproduits ici. [R4]

### Références complémentaires

GutenOCR fournit la formulation multitâche lecture/localisation/requête conditionnelle [R5]. DAN montre une voie de lecture documentaire avec structure logique sans segmentation externe imposée [R6]. Hierarchical Text Spotter articule plusieurs niveaux spatiaux [R7]. Deformable DETR fournit un principe de consultation sparse de caractéristiques visuelles [R8]. LevOCR est pertinent plus tard pour une révision par opérations d'édition, sans justifier son ajout au prototype [R9].

**Conséquence scientifique :** ne pas revendiquer comme invention le seul fait de partager un encodeur, d'ajouter une tête géométrique ou d'intercaler texte et coordonnées. La contribution possible doit porter sur les contraintes, la précision, le transfert, la correction et l'économie réellement démontrées.

## 3. Hypothèses et variables à isoler

### H1 : accessibilité de la géométrie

Les représentations du lecteur permettent de localiser les occurrences d'une transcription imposée sur des documents nouveaux.

**Falsificateurs :** bonne performance uniquement sur le train ; dépendance essentielle à la géométrie de référence ; confusion des occurrences répétées ; résultat inchangé lorsque la correspondance image-caractéristiques est détruite.

### H2 : utilité du détail visuel

L'accès aux caractéristiques fines améliore la géométrie par rapport aux seuls états du lecteur, à résolution et budget d'entraînement comparables.

**Falsificateurs :** gain expliqué par davantage de pixels, de paramètres ou de pas d'entraînement ; gain limité aux très grands mots ; absence de progression sur les frontières difficiles.

### H3 : couplage utile pour la lecture

La consultation spatiale injectée avant les décisions textuelles améliore la lecture libre ou permet un meilleur compromis qualité/coût.

**Falsificateurs :** CER inchangé et calcul accru ; progrès uniquement sous transcription fournie ; coordonnées meilleures mais davantage de chiffres ou de mots inventés.

### H4 : utilité marginale en correction

Avec des observations ALTO/PAGE existantes, le même noyau peut traiter les passages réellement incertains sans dégrader les parties conservées.

**Falsificateurs :** déplacement de mots inchangés ; modification d'un champ verrouillé ; recours au modèle sur toute la page pour une correction locale alors que la nouvelle information ne le justifie pas.

## 4. Architecture candidate

### 4.1 Point de départ

Utiliser un backbone ouvert instrumentable, proposé ici : `Qwen/Qwen3-VL-2B-Instruct`, à révision immuable. C'est un support de recherche, pas une affirmation de supériorité OCR. Sa fiche affiche Apache-2.0. La configuration inspectée indique une dimension texte de 2048, une dimension vision de 1024, des patches de 16 et une fusion spatiale de facteur 2. [R10, R11]

Qwen3-VL exploite déjà des caractéristiques multiniveaux via DeepStack. L'ablation doit donc comparer le candidat au backbone natif complet, pas à une version artificiellement privée de cette capacité. [R12]

Une API de lecteur fermé ne permet pas cette instrumentation. Des lectures externes peuvent contribuer à des annotations de travail, mais elles ne doivent pas devenir une dépendance du candidat final ni une référence considérée exacte sans contrôle.

### 4.2 Perception commune

Conserver la sortie compacte normale et une carte visuelle fine déjà calculée avant fusion. Pour le premier essai, une seule carte fine suffit ; empiler toutes les couches augmenterait les dimensions de recherche avant de montrer leur utilité.

La carte doit rester associée à une transformation exacte vers la page originale. Il faut reconstruire l'ordre spatial réel des patches depuis le traitement du modèle, et ne pas supposer qu'un simple reshape retrouve automatiquement la bonne grille.

La mémoire avant fusion ne contient que ce qui survit au redimensionnement d'entrée. Aucun localisateur ne restaure une distinction graphique absente des pixels présentés. À l'inverse, la taille des patches n'est pas à elle seule une quantification dure des coordonnées : des offsets continus peuvent exploiter une information intra-patch.

### 4.3 Représentation d'une occurrence

Une occurrence est indexée par un intervalle dans une transcription versionnée, pas par sa chaîne seule. Deux `de` dans la même ligne ont des identités distinctes.

Le paquet de propositions pourrait porter : identifiant local ; texte ou intervalle textuel ; rattachement proposé ; géométrie éventuelle ; statut de correspondance ; version de texte ; version du modèle ; transformation image/page.

Séparer trois grandeurs : confiance de reconnaissance, incertitude de localisation, risque d'omission. Une boîte correcte autour de `1780` ne prouve pas que la lecture `1789` est justifiée.

### 4.4 Sonde géométrique, première version

Fournir la transcription connue, obtenir les états du décodeur et construire une requête par occurrence à partir de ses sous-tokens. Projeter requêtes et carte fine dans une dimension commune proposée de 256. Utiliser initialement une attention croisée dense avec positions 2D : elle est plus facile à inspecter qu'un échantillonneur sparse.

La sortie initiale prédit un rectangle et un score à calibrer. La référence comparable est une tête qui ne reçoit que les états textuels. Les caractères d'un mot ne doivent pas être supposés équidistants pour fabriquer la vérité géométrique.

L'emploi d'une transcription fournie est légitime dans le mode alignement. Il ne démontre pas une lecture libre réussie.

### 4.5 Couplage, deuxième version

Introduire le module de consultation dans une couche du décodeur avant sa sortie textuelle. Le signal visuel récupéré modifie l'état qui prédit le token suivant. Un coefficient de résidu initialement nul permet de commencer sans perturber brutalement le lecteur ; les modules spatiaux reçoivent une supervision propre.

Comparer ce couplage à la sonde placée après lecture. Une meilleure géométrie après coup et une meilleure lecture grâce à la géométrie sont deux résultats différents.

Les caractéristiques de perception restent partagées. On ne relance pas un recognizer indépendant. Si la consultation dense devient coûteuse, tester un échantillonnage local appris, sans cumuler les deux au déploiement. L'optimisation sparse vient après la preuve d'utilité.

### 4.6 Forme des boîtes

Commencer avec des rectangles pour le lot de blocs faiblement inclinés. Documenter cette limitation. Le passage aux quadrilatères ou courbes nécessite des annotations compatibles ; ne pas fabriquer une supervision polygonale précise à partir de rectangles lâches.

Comparer de manière bornée une sortie continue et une sortie discrète à même backbone. Le choix reste expérimental. Si une grille possède K intervalles sur une largeur W, l'arrondi au plus proche introduit au plus W/(2K) d'erreur par coordonnée : pour W=6000 et K=1000, 3 pixels ; sur un crop W=500, 0,25 pixel. Ce calcul ne mesure pas l'erreur apprise.

## 5. Détails d'implémentation qui peuvent invalider une expérience

### Correspondance sous-tokens, mots, graphèmes

Conserver le texte diplomatique et une table d'offsets. Le découpage du tokenizer n'est pas la définition documentaire du mot. Vérifier accents composés/décomposés, apostrophes, ligatures, signes historiques, tirets et césures. Pour un tokenizer dont les offsets ne sont pas assez fiables, construire la correspondance par décodage contrôlé et vérifier la reconstruction exacte.

### Décalage causal des états

L'état calculé après avoir consommé un token prédit le suivant. La requête du mot complet doit être construite après consommation de ses sous-tokens, pas confondue avec l'état ayant prédit son premier token. Un minuscule test traçant les positions doit établir la convention utilisée.

Pour le couplage de lecture, ne pas donner à la requête la fin du mot qui n'a pas encore été générée. Sinon l'expérience bénéficie d'une information indisponible à l'inférence.

### Teacher forcing et génération

Rapporter trois conditions : transcription correcte imposée ; transcription partiellement fausse imposée ; lecture libre. Ne jamais remplacer le préfixe produit par la vérité terrain pendant l'évaluation libre. Ne pas rejouer la transcription de référence pour produire les boîtes d'un résultat qualifié de bout en bout.

### Images et coordonnées

Enregistrer crop, échelle, padding, dimensions originales, convention de coordonnées et toute transformation de perspective. Utiliser une convention semi-ouverte cohérente avec BBVLM. Tester un aller-retour exact avant arrondi, puis un arrondi explicite à l'export.

### Cache

Un cache de caractéristiques doit inclure la révision des poids, l'image, le processor, la résolution et l'augmentation. Il devient invalide quand les poids produisant ces caractéristiques changent. Le cache de replay ne réduit pas le coût d'une nouvelle page en production.

### Fonctions d'échantillonnage

Si `grid_sample` est utilisé, fixer explicitement sa convention de normalisation et `align_corners`. Des tests géométriques doivent vérifier coins, centres et bords. Les éventuelles limites de reproductibilité du backend doivent être consignées. [R14]

## 6. Corpus et supervision

### Propositions de volumes

Les volumes ci-dessous sont des enveloppes de départ, pas des tailles universellement suffisantes.

| Lot | Taille proposée | Fonction |
|---|---:|---|
| Débogage | 64 crops | Vérifier offsets, transformations, perte et surapprentissage contrôlé |
| Apprentissage réel initial | 3000 à 6000 lignes | Apprendre la correspondance sur plusieurs dizaines d'ouvrages/titres |
| Synthétique initial | 10000 à 30000 lignes ou petits blocs | Géométrie exacte et interventions contrôlées |
| Développement | 500 à 1000 lignes, documents distincts | Choisir architecture et paramètres |
| Calibration | Lot séparé si un seuil de risque est publié | Choisir les seuils sans regarder le test final |
| Test final | Au moins 1000 lignes, documents et titres séparés | Mesurer le transfert, sans prétendre certifier d'emblée des risques extrêmement rares |

Ne pas multiplier le nombre de lignes d'un seul ouvrage pour faire croire à une diversité documentaire. Les titres, ouvrages, éditions et templates apparentés doivent rester dans la même partition. Le synthétique réserve également des fontes et des contenus.

### Niveau de fiabilité par annotation

- Texte seul vérifié : appliquer la perte de texte, masquer les pertes géométriques sans référence valable.
- Texte et lignes vérifiés : exploiter la localisation de ligne, sans inventer les boîtes de mots.
- Boîtes automatiques : supervision faible avec provenance et poids explicites.
- Mots géométriquement vérifiés : supervision forte et évaluation.
- Référence contestée : garder l'original et l'adjudication séparés ; ne pas choisir la version qui favorise le modèle.

Une pondération indicative peut être étudiée sur développement, mais ne pas choisir arbitrairement un poids universel pour les pseudo-étiquettes. Publier une ablation avec et sans celles-ci.

### Convention de boîte

Définir avant annotation si la ponctuation appartient au mot précédent, comment traiter les traits d'union, les espaces internes, les glyphes isolés et les ligatures. Noter si la boîte est une enveloppe d'encre ou un intervalle typographique. La tolérance inter-annotateurs est une mesure utile, pas un prétexte pour retirer les cas difficiles.

### Difficultés prioritaires

Répétitions proches ; petits mots ; chiffres/noms propres ; début/fin de ligne ; lettres ou accents isolés ; espaces de justification ; césures ; lignes inclinées ; titres très espacés ; colonnes proches ; encre faible ou traversante. Ne pas limiter les exemples difficiles aux erreurs de l'ancien moteur : constituer aussi un échantillon aléatoire stratifié.

### Références négatives

Créer des couples dont la relation est connue : remplacer un mot par une chaîne absente, permuter deux occurrences, déplacer une ligne dans le synthétique, masquer un passage, présenter la même phrase avec une mise en page différente. Les paires négatives réelles doivent être vérifiées pour ne pas étiqueter absent un mot qui figure ailleurs.

Une transcription erronée peut garder une localisation partielle pertinente. Pour `1789` demandé sur une image de `1780`, conserver la distinction entre « région du passage trouvée » et « chaîne justifiée ». Ne pas apprendre un refus global automatique dès qu'un caractère diffère.

## 7. Expériences, ordre et critères de décision

### E0. Instrumentation et référence native

**Question :** les états et caractéristiques récupérés correspondent-ils aux bons pixels et tokens ?

**Travail :** exécuter le backbone natif ; brancher l'observation sans modification de sortie ; tester reconstruction textuelle, transformation des coordonnées et parité des sorties ; mesurer VRAM et temps sur quelques blocs.

**Réussite :** aucune altération de la sortie native au-delà d'une tolérance numérique définie ; conventions traçables ; coûts enregistrés.

**En cas d'échec :** corriger l'instrumentation, sans entraîner une tête sur des états mal associés.

### E1. Accessibilité géométrique

**Bras :** G0, géométrie de référence existante de BBVLM ; G1, états du lecteur seuls ; G2, mêmes états et carte fine. G0 est un comparateur hors du chemin du candidat. Les candidats reçoivent les mêmes textes et images.

**Évaluation :** frontières internes, IoU, début/fin de ligne, répétitions, p95/p99, taux d'échecs. Train et développement sont séparés par document.

**Décision :** retenir G2 seulement si l'accès visuel apporte un gain hors train. Une bonne capacité à mémoriser les 64 crops ne suffit pas. Si G1/G2 échouent après débogage, autoriser une adaptation limitée avant de conclure sur l'accessibilité des représentations.

### E2. Contrôles de dépendance visuelle

**Interventions :** image incorrecte ; carte fine spatialement permutée ; neutralisation de l'accès fin ; déplacement/échelle de la même composition ; même texte avec géométrie différente.

**Réussite :** sur les données appariées contrôlées, la géométrie suit la transformation connue. Le simple effondrement sur une image bruitée ne suffit pas à prouver un ancrage correct.

**Décision :** si le gain vient surtout de régularités textuelles ou de positions mémorisées, améliorer les paires d'entraînement et les contrôles, sans annoncer un succès de grounding.

### E3. Couplage de la lecture

**Bras :** lecteur natif ; lecteur avec sonde après lecture ; lecteur avec consultation fine avant la prédiction. Mêmes pixels, textes d'entraînement et budget comparable. Conserver les fonctionnalités visuelles natives du backbone.

**Mesures :** CER diplomatique, insertions, chiffres, omissions, correspondance texte+boîte, coût réel. Mesurer la perte de teacher forcing uniquement comme diagnostic, jamais comme substitut à la lecture libre.

**Réussite :** gain conjoint ou meilleur compromis qualité/coût, sans augmentation non acceptée d'erreurs critiques.

**Décision :** si seule la géométrie progresse, le résultat reste intéressant, mais l'hypothèse « la localisation aide la lecture » n'est pas démontrée. Ne pas garder un couplage plus complexe sans bénéfice observé.

### E4. Correspondances douteuses et abstention

**Question :** le modèle distingue-t-il un passage visible, partiellement compatible et non localisable ?

**Travail :** exemples négatifs vérifiés ; calibration séparée ; inspection des faux accords image-texte ; mesure risque/couverture.

**Réussite :** baisse de l'erreur parmi les sorties acceptées avec couverture explicitement rapportée. La calibration est évaluée sur le domaine déclaré, sans prétendre la garantir sur une autre fonte ou un autre siècle.

### E5. Blocs et exhaustivité

**Question :** le modèle retrouve-t-il les unités sans boîtes de ligne fournies ?

**Travail :** blocs complets ; lignes voisines ; début/fin ; doublons ; sortie de structure minimale. La même mémoire visuelle sert à l'assignation de ligne. Une éventuelle supervision de présence de lignes doit appartenir au même modèle, pas lancer un autre OCR.

**Point crucial :** les sorties absentes n'ont pas de score d'incertitude. Il faut donc mesurer directement la couverture du document, pas seulement la confiance des mots produits.

**Décision :** si les mots émis sont précis mais les omissions élevées, le modèle est un localisateur conditionnel utile, pas encore un lecteur documentaire exhaustif.

### E6. Révision contrainte et export

**Question :** les mêmes poids peuvent-ils utiliser des observations existantes sans les détruire ?

**Travail :** substitutions 1→1 ; scissions/fusions ; texte intégralement remplacé ; mots verrouillés ; propositions incertaines. Ne pas envoyer au modèle toutes les substitutions dont la géométrie peut être conservée déterministement.

**Réussite :** invariants logiciels exacts, résultats neuronaux mesurés, provenance complète, aucun statut `human_verified` donné par le modèle.

## 8. Programme d'entraînement proposé

### Phase A : gel complet

Entraîner seulement la tête/requête de grounding sur des représentations figées. Choisir un budget borné de variantes, par exemple dimension 256 et deux variantes de couche, plutôt qu'une recherche combinatoire.

### Phase B : adaptations limitées

Ajouter LoRA dans un sous-ensemble explicitement choisi du décodeur si le diagnostic le justifie. Ne pas démarrer en mettant à jour tous les paramètres. LoRA est une technique d'adaptation ; son économie mémoire ne dispense pas de mesurer les activations. [R13]

### Phase C : apprentissage conjoint

Mélanger lecture libre, transcription conditionnelle et cas négatifs. Proposer initialement un mélange à trois familles, puis le figer après une étude de développement. Ne pas traiter un mauvais texte imposé comme une vérité à recopier : le masque de perte doit séparer demande, correction et support.

### Phase D : difficulté spatiale

Introduire blocs et perturbations de géométrie de manière progressive. Les augmentations entraînement changent les annotations quand elles déplacent les pixels. Les augmentations purement photométriques ne doivent pas changer la position nominale, tout en pouvant rendre la lecture incertaine.

### Discipline

Deux graines pour trier les variantes sur développement peuvent constituer un premier budget. Relancer le candidat final sur trois graines avant de publier une comparaison, si les moyens le permettent. Le modèle choisi et ses seuils doivent être gelés avant le test indépendant. La variabilité inter-documents reste plus importante à vérifier que la seule variabilité entre graines.

## 9. Mesures et pièges statistiques

### Fidélité textuelle

CER NFC strict sous convention diplomatique ; WER ; insertions, suppressions, substitutions ; exactitude des chiffres et noms propres ; taux d'omission de lignes. Une vue normalisée peut être publiée en plus, jamais remplacer le texte diplomatique pour faire disparaître les erreurs.

### Géométrie conditionnelle

Employer les critères historiques de BBVLM, dont frontières à 0,5 caractère, pire cas, IoU médiane et non-régression par corpus. Garder les échecs et abstentions dans le bilan global. Ne pas noter seulement les mots que le modèle a réussi à lire.

### Résultat conjoint

Définir avant les expériences un appariement un-à-un entre occurrences produites et références. Compter faux positifs, faux négatifs, texte incorrect et localisation incorrecte. Les répétitions ne se résolvent pas par une correspondance lexicale globale. Publier à la fois métriques jointes et métriques séparées.

### Géométrie acceptable versus texte justifié

Une correspondance spatiale peut être exacte même si le texte est faux. Les scores de support doivent être évalués sur les couples image-texte, pas réétiquetés positifs sur le seul IoU.

### Incertitude statistique

Comparer les candidats sur les mêmes pages. Rééchantillonner les unités documentaires pertinentes pour les intervalles de confiance : un ensemble de mille mots du même journal n'est pas mille documents indépendants. Rapporter corpus et familles typographiques séparément.

Zéro erreur sur N essais ne signifie pas risque nul. Sous une hypothèse simplifiée d'indépendance, la borne supérieure unilatérale à 95 % après zéro erreur est environ 3/N. Cette approximation ne justifie pas de certifier un risque de 0,1 % avec quelques dizaines de mots, et la corrélation documentaire rend l'extrapolation encore plus délicate.

Le maximum dépend de l'effectif. Garder le critère historique sur les jeux comparables, et publier aussi p99 et le taux de dépassement d'un seuil critique sur les grands ensembles. Ne pas réviser rétroactivement un critère parce qu'un candidat le rate.

### Utilité humaine

Sur un lot aveugle, mesurer minutes de relecture par page, corrections de texte, reprises de boîtes et erreurs résiduelles après relecture. Répartir les pages et l'ordre des candidats pour éviter qu'un annotateur lise la même page plusieurs fois et bénéficie de sa mémoire. Les hypothèses de coût sont remplacées par ces temps observés.

## 10. Intégration exacte à BBVLM

Le code consulté de `src/bbvlm/document.py` expose `bbvlm.document/1`, des coordonnées pixels semi-ouvertes, les statuts `automatic`, `pending`, `ambiguous`, `rejected`, `human_verified` et des nœuds page/région/ligne/mot. Son validateur exige actuellement une boîte valide sur chaque nœud. [C2]

**Conséquence :** ne pas injecter directement des mots à géométrie nulle dans `nodes`. Conserver les occurrences non localisées dans un paquet de propositions distinct, avec leur intervalle textuel et leur motif. La ligne existante reste visible et peut porter `needs_alignment`.

Le chemin `apply_proposal` invalide actuellement les anciennes boîtes de mots lorsqu'un texte change. Une sortie conjointe texte-géométrie demandera une opération atomique explicite : contrôler version du texte, identifiants, coordonnées et verrouillages avant de modifier le graphe. Ne pas appeler successivement deux écritures qui pourraient laisser un document à moitié mis à jour. [C2]

Le futur adaptateur peut conserver le schéma public actuel au début. Une extension de schéma ne devrait être proposée qu'après avoir établi le besoin, avec migration et tests.

Les anciennes boîtes ne doivent pas être certifiées justes parce qu'elles sont conservées. Leur conservation évite une modification inutile ; elle préserve aussi leur statut et leur provenance.

## 11. Organisation technique minimale

Organisation proposée, non créée dans le dépôt :

```text
src/bbvlm/neural/
    backbone.py        # accès contrôlé aux représentations
    occurrences.py     # correspondance texte/sous-tokens/occurrences
    grounding.py       # tête et consultation visuelle
    objectives.py      # pertes et masques de supervision

experiments/joint_grounding/
    protocol.yaml
    manifests/
    configs/
    train.py
    evaluate.py
    reports/
```

Conserver un extra de dépendances neural. L'import et l'export documentaires CPU ne doivent pas exiger le téléchargement des poids. Utiliser PyTorch, Transformers, PEFT lorsque nécessaire, les outils image usuels et les tests existants. Éviter un nouveau serveur ou orchestrateur d'expériences tant qu'un programme d'entraînement simple suffit.

Enregistrer révision backbone, révision tokenizer/processor, paramètres, versions, manifeste de données, graine, transformations, métriques et coûts. Pas de dépendance flottante `main` dans une expérience gelée. Un notebook peut servir à inspecter ; le run de référence doit être rejouable par script.

## 12. Budget de travail et de calcul

Calendrier indicatif pour une personne technique disponible et un accès GPU régulier. Ce n'est pas une garantie de résultat ni un délai de production institutionnelle.

| Période | Travail | Résultat attendu |
|---|---|---|
| Semaine 1 | Corpus, conventions, instrumentation, profilage | E0 et protocole figé |
| Semaines 2–3 | Sonde et contrôles visuels | Décision H1/H2 |
| Semaines 4–6 | Couplage et génération libre | Décision H3 |
| Semaines 7–9 | Blocs, omissions, négatifs, calibration | Domaine de validité défini |
| Semaines 10–12 | Révision contrainte, test gelé, relecture | Démonstrateur et rapport |

Les défauts de données ou d'annotation peuvent dominer ce calendrier. Une validation patrimoniale large demandera des cycles supplémentaires. Ne pas promettre un système universel en douze semaines.

### Profilage avant réservation

Mesurer sur 50 à 100 blocs : VRAM de pointe, temps d'encodage, préremplissage, décodage, grounding, export. Pour l'entraînement, mesurer la moyenne du temps par pas après échauffement et l'extrapoler au nombre de pas envisagé. Distinguer inférence, entraînement, préparation et relecture.

Le coût de quatre coordonnées prédites par une petite tête n'est pas celui de quatre tokens décodés à travers tout le modèle. Le cache visuel ne supprime ni la mémoire KV ni le coût autoregressif. Le coût par page doit inclure tuiles, recouvrements et reprises.

Le premier objectif matériel est un run monogpu sur petits blocs, avec backbone gelé puis adaptation limitée. Aucune capacité précise de GPU n'est présumée disponible. Ne pas choisir le plein entraînement ni le multi-GPU avant le profilage.

## 13. Table de diagnostic : quoi faire après un échec ?

| Observation | Interprétation à vérifier | Action prioritaire |
|---|---|---|
| Le train ne descend pas | Bug offsets, transformation, masque ou optimisation | Corriger E0 sur 64 exemples |
| Train excellent, documents nouveaux mauvais | Raccourci typographique ou faible diversité | Revoir split, données et contrôles |
| Sonde bonne, lecture libre mauvaise | Dépendance au texte fourni ou erreurs cumulées | Évaluer génération et adaptation textuelle |
| Boîtes bonnes, chiffres faux | Localisation sans justification textuelle | Négatifs ciblés et consultation avant décision |
| Petite police mauvaise dans tous les bras | Résolution ou capacité visuelle insuffisante | Étude contrôlée de résolution, sans nouvelle cascade |
| Omissions de lignes | Couverture absente, pas seulement confiance | Apprentissage structure/couverture dans le même modèle |
| Couplage plus cher sans gain | Intégration inutile dans ce domaine | Garder le modèle plus simple, ne pas l'enrichir pour sauver l'hypothèse |
| Pas de bénéfice malgré données et adaptation contrôlées | Backbone peut-être inadéquat | Examiner une architecture compacte orientée spotting comme remplacement, pas comme maillon supplémentaire |

## 14. Définition du succès et de la contribution possible

Un résultat utile doit montrer, sur des données nouvelles, soit une amélioration de qualité à coût comparable, soit une économie mesurée sans dégradation non acceptée. Le système doit garder un domaine déclaré, traiter les sorties non résolues et préserver les garanties documentaires.

La contribution possible est une lecture ancrée à précision fine, utilisable aussi sous transcription ou géométrie partiellement imposées, avec une mesure des erreurs extrêmes et de l'effort humain. Le mécanisme seul n'est pas présumé nouveau ; une recherche d'antériorité plus large devra précéder toute revendication de nouveauté.

## 15. Les trois premiers livrables

1. **Contrat d'expérience** : définition d'occurrence, texte diplomatique, boîtes, versions, inconnues, partitions et critères.
2. **64 exemples traçables** : pixels, texte, offsets, transformations et annotations contrôlées ; banc qui repère les erreurs d'indexation et de géométrie.
3. **Sonde comparée** : états du lecteur seuls contre accès à la carte fine, avec contrôle d'image permutée, rapport par occurrence et coût complet.

Pas de nouveau moteur à installer à l'issue de cette étape. La décision porte sur le mécanisme à poursuivre.

## Références publiques

Les résultats des articles sont ceux rapportés par leurs auteurs ; ils ne sont pas reproduits dans ce dossier. Les propositions de notre plan ne sont pas des résultats attribués à ces sources.

- **R1.** Mao et al., *Visually Guided Generative Text-Layout Pre-training for Document Intelligence*, NAACL 2024. Version conférence : https://aclanthology.org/2024.naacl-long.264/ ; méthode détaillée consultée dans la prépublication : https://arxiv.org/html/2403.16516v1
- **R2.** *DeepSolo++: Let Transformer Decoder with Explicit Points Solo for Multilingual Text Spotting*. https://arxiv.org/html/2305.19957v2
- **R3.** *PILOT: A Promptable Interleaved Layout-aware OCR Transformer*, version 2. https://arxiv.org/html/2504.03621v2
- **R4.** Chai et al., *State-Conditioned Visual Evidence Retrieval for Fine-Grained Perception in Document Vision-Language Models*, prépublication du 27 août 2026. https://arxiv.org/html/2608.28698v1
- **R5.** Heidenreich et al., *GutenOCR: A Grounded Vision-Language Front-End for Documents*, 2026. https://arxiv.org/html/2601.14490v1
- **R6.** Coquenet et al., *DAN: a Segmentation-free Document Attention Network for Handwritten Document Recognition*. https://arxiv.org/abs/2203.12273
- **R7.** *Hierarchical Text Spotter for Joint Text Spotting and Layout Analysis*. https://arxiv.org/abs/2310.17674
- **R8.** Zhu et al., *Deformable DETR: Deformable Transformers for End-to-End Object Detection*. https://arxiv.org/abs/2010.04159
- **R9.** *Levenshtein OCR*, ECCV 2022. https://arxiv.org/html/2209.03594v2
- **R10.** Qwen, fiche `Qwen3-VL-2B-Instruct`. https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct
- **R11.** Configuration du checkpoint, à épingler par révision avant le premier run. https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct/blob/main/config.json
- **R12.** Documentation officielle Transformers, Qwen3-VL. https://huggingface.co/docs/transformers/model_doc/qwen3_vl
- **R13.** Documentation officielle PEFT, LoRA. https://huggingface.co/docs/peft/developer_guides/lora
- **R14.** Documentation officielle PyTorch, `grid_sample`. https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.grid_sample.html

## Sources de projet consultées

Consultation de fichiers précis, pas audit intégral du dépôt. Les références de branche sont mobiles ; les blobs ci-dessous identifient les contenus lus.

- **C1.** `BBVLM/experiments/loop/ARCHITECTURE_A19.md`, branche `codex/autonomous-research-a34`, blob `f7cbbd0f497ebc146753ba90f8f9208b4328db0a`.
- **C2.** `BBVLM/src/bbvlm/document.py`, même branche, blob `71546a97d4274945bb348ea90d4c6925c9d6d890`.
- **C3.** `BBVLM/IMPLEMENTATION.md`, même branche : documentation d'implémentation consultée comme contexte, dont certaines sections décrivent des étapes historiques.
- **C4.** Arborescence `BBVLM/src/bbvlm/`, même branche : modules `document.py`, `formats.py`, `metrics.py`, `ocr_conventions.py`, `binding.py` présents au moment de la consultation.

Les critères historiques repris dans ce plan proviennent de `CRITERE.md` lu dans la conversation. Leur gel reste distinct de l'approbation du nouveau protocole : aucun critère ancien n'est modifié par ce document.
