# Lecture directe de page — convention v2, avant essais

Le 6 octobre 2026, l'utilisateur précise que les accents et normalisations
typographiques ne comptent pas dans son appréciation du CER. Cette nouvelle
convention s'applique aux nouveaux essais de lecture directe de page. Les
anciens scores stricts et de convention v1 restent inchangés et disponibles.
Les critères de géométrie, couverture et OLR restent ceux de PROTOCOLE.md.

Gemini reçoit uniquement l'image originale de la page, sans segmentation,
texte ou coordonnées de référence. Il produit tout le texte en Markdown.
BBVLM conserve ce résultat NFC avant la géométrie. Une difficulté de placement
ne retire jamais du texte de cet artefact. Le score de la VT complète reste
distinct de celui des mots effectivement placés et exportables en ALTO.

Pour la notation textuelle, la conversion du Markdown en texte retire les
marqueurs de présentation de titres, emphase et listes ; leur contenu reste.
La ponctuation contenue dans le texte reste mesurée. Un tableau conserve
toutes ses cellules et leur ordre ; les dessins et séparateurs sans texte
relèvent de l'OLR. Le convertisseur et sa version figurent dans le rapport.
Les paragraphes et retours imprimés sont conservés dans l'artefact ; une
seconde mesure neutralise les seuls espaces Unicode pour comparer le texte
d'une page indépendamment de sa présentation. L'ordre reste mesuré.

La convention v2 applique la convention v1, puis NFKD, retire les marques
Unicode combinantes (catégories M), et développe œ/Œ et æ/Æ en oe/OE et ae/AE.
NFKD développe aussi les ligatures de composition et le s long. Casse,
graphies lexicales, chiffres et ponctuation ne deviennent pas équivalents.
La cédille est une marque combinante et relève de la même règle annoncée.
Aucune substitution point/virgule, aucune correction de mot, aucun déplacement
ou suppression de texte supplémentaire n'est autorisé par la notation.
La production conserve tous les caractères visibles : la normalisation v2
est exclusivement une fonction d'évaluation.

Publier le CER strict NFC, le CER v1 historique, le CER v2, leurs erreurs
absolues, les caractères de référence, incertitudes et pages manquantes.
Comparer sur la suite fixe entière (5 dev, 16 réservées), sans sélection selon
le résultat. La référence ordonnée est chargée seulement par l'évaluateur
indépendant après sauvegarde de la production. Le score ne démontre pas à lui
seul la correspondance spatiale, l'ordre des blocs ni les articles.

Pour isoler la lecture de l'ordre, un diagnostic supplémentaire apparie les
lignes imprimées transcrites et les lignes de référence par coût textuel
minimal, un-à-un, uniquement dans l'évaluateur. Toutes les suppressions et
insertions, y compris les lignes sans correspondance, restent comptées.
Publier les couples et leurs inversions. Cet appariement optimiste n'est pas
un score de segmentation ni une preuve d'ordre correct ; il ne remplace pas
le CER de page ordonnée. Un changement des retours imprimés peut dégrader ce
diagnostic et doit être signalé, sans recomposer la référence en production.

La conversion HTML conserve le contenu et les attributs alt visibles des
images ; les balises inconnues sont conservées et signalées. Publier aussi
strict_NFC_whitespace : seul l'espacement varie, les accents et apostrophes
restent strictement distingués. Le convertisseur porte une révision explicite.

## Variante native v2, déclarée avant essais

La réponse est désormais du Markdown naturel, sans JSON, modèle autodéclaré,
découpage en segments ou contrainte de retours imprimés. Le UUID et le prompt
exact sont liés à l'étape native de réponse terminée. L'adaptateur agy 1.2.17
lit seulement le texte final du planner (champs protobuf 20.1 et 20.8 égaux),
après la lecture des images, en excluant pensées et appels d'outils. Un schéma
incompatible produit un arrêt récupérable, sans nouveau prompt de formatage.
Le modèle est attesté par l'affichage natif Gemini, pas par une déclaration
du modèle. L'incertitude signale seulement les marqueurs [illisible] déclarés,
pas une certification de qualité en leur absence.

La page entière donne le contexte ; des vues régulières de 1536 × 1536 pixels,
avec chevauchement 192 pixels, donnent le détail. Les bords sont couverts et
les crops conservent exactement les pixels source, sans segmentation de texte.
Tous les chemins et empreintes figurent dans la requête. Cette variante change
le format de réponse ET l'entrée visuelle : un gain ne permet pas d'attribuer
séparément l'effet à chacun. Les essais v1 restent disponibles, y compris les
pages non exécutées, comptées manquantes. La suite fixe ne change pas.

Le diagnostic d'appariement des lignes hors ordre devient fragile avec des
paragraphes reformatés : le CER de page et ses erreurs absolues restent publiés.
Une référence incomplète ou un ordre éditorial ambigu reste signalé dans le
verdict ; aucun texte supplémentaire n'est supprimé pour améliorer le score.

## Périmètre textuel de référence, chargeur v2

Les nouvelles notes de VT entière lisent toutes les TextLine non vides du
PAGE, y compris celles des TableCell, même sans coordonnées. Le chargeur
historique limité aux lignes directes de TextRegion reste inchangé pour les
anciens diagnostics et la géométrie. Les rapports distinguent les versions.
L'ordre suit les RegionRefIndexed déclarés, puis custom, puis le document.
Une table absente de l'ordre explicite est signalée comme ordre incomplet ;
son texte reste compté. Aucun ordre de référence n'est adapté à la prédiction.
Les lignes vides, doublons d'IDs et lignes sans coordonnées sont comptées dans
l'audit. Des textes visibles non annotés restent des insertions dans le score
strict, avec l'anomalie de périmètre signalée ; ils ne sont pas censurés.

## Livraison par portions v3, déclarée avant le nouvel essai

La variante v2 a conservé une réponse de 26 758 caractères, suivie d'une erreur
native et d'un refus de transcription intégrale. Ce texte partiel reste évalué
avec toutes les omissions. La variante v3 conserve la lecture de page entière
et le Markdown naturel, mais demande environ 6 000 caractères par réponse.
Chaque portion porte un UUID, un marqueur MORE, END ou REFUSED et une preuve
native. La suite reçoit uniquement la fin de la VT précédente comme ancre,
jamais une référence. La première image est attestée par un Read natif achevé
dans le même contexte ; une suite sans nouvelle lecture doit se rattacher à
ce Read exact. Cette variante revient à l'image globale seule : elle change
donc aussi l'entrée par rapport aux 48 vues de v2, sans attribution causale
isolée de ses effets. La réduction client documentée reste une limite.

Les portions sont conservées séparément avec leurs empreintes. La VT NFC
concatène leurs contenus dans l'ordre reçu, sans correction, dédoublonnage
ou suppression de mots. Elle existe dès la première portion et son statut
reste partiel tant que END n'est pas reçu. END est une assertion du lecteur,
pas une certification de couverture. Un refus, une interruption ou un contrat
invalide laisse les textes reçus et les bruts disponibles ; un timeout seul
autorise uniquement leur récupération. Les pages manquantes et les textes
omis restent comptés. Les critères et conventions de notation ne changent pas.

## CER HIPE-OCRepair / ICDAR 2026 — demande du 7 octobre

Le mode `hipe_ocrepair_2026` reproduit `norm()` du scorer officiel, vérifié
sur la référence entière et la sortie Gemini entière. La provenance du code
de normalisation (URL, date, SHA-256) accompagne le rapport. Il applique la
mise en minuscules, les équivalences historiques et ligatures explicites,
les marqueurs de césure `—` ou `¬` suivis d'un saut de ligne, puis remplace
ponctuation et symboles par des espaces et compacte les espaces. Les accents
restent distincts. Ce profil ne doit pas être confondu avec `convention_v2`,
qui enlève les accents et reste conservé comme mesure historique.

Le CER est `(substitutions + suppressions + insertions) / caractères de
référence normalisés`, distinct du cMER de classement HIPE. Il est calculé
sur toute la sortie Gemini, avant les exclusions géométriques. L'ordre des
paragraphes, les omissions et les ajouts comptent ; un ordre de référence
incomplet est signalé dans `reference_text_audit`, sans réordonner la référence
en fonction de la prédiction. Aucune référence n'est fournie à la production.

## Essai minimal v4 demandé par l’utilisateur

Le prochain essai abandonne la pagination dans le prompt et les vues multiples.
La demande est exactement « Je veux l’OCR complet de cette page en Markdown. »
avec le chemin de l’image source. Le contexte est vierge pour chaque page.
L’UUID reste dans le cache BBVLM ; le prompt humain natif exact, sa date après
préparation, le Read de source et le CID unique lient la réponse au job.
Les réponses partielles et erreurs natives restent signalées et évaluées.
Ce changement répond à la préférence explicite transmise par Astra ; les
essais précédents, omissions, critères et conventions restent conservés.

## Politique de transcription : fidélité à l'imprimé (décision de Marcel, 17/10/2026)

Gemini recopie l'imprimé tel qu'il est, coquilles comprises : lettre fautive,
retournée ou abîmée, mot coupé en fin de ligne dont chaque moitié est gardée
telle qu'imprimée. Il ne corrige pas un mot d'après le sens ni d'après le mot
recollé. La consigne de `scripts/transcrire_regions.py` le dit explicitement
depuis cette date ; les transcriptions antérieures ne sont pas rejouées. Dans
le rapport d'écarts, une correction silencieuse de Gemini compte donc comme un
écart à l'imprimé (catégorie `correction_gemini`), pas comme un succès.
