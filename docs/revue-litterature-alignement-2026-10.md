# Revue de littérature : produire une vérité terrain OCR de presse ancienne en alignant un VLM sur des lignes détectées

Date : 18 octobre 2026. Périmètre : 2023-2026 en priorité, classiques rappelés.
Méthode : recherche web (titres, résumés, pages d'éditeurs, PDF quand lisibles). **Je n'ai lu en texte intégral que le papier HIPE-OCRepair 2026 ; pour tous les autres, je m'appuie sur le résumé ou la page de description.** Les chiffres sont donnés tels que lus ; ceux qui viennent d'un résumé secondaire sont signalés « (à vérifier) ». Rien n'est inventé : ce qui n'a pas pu être vérifié est dans la section 10.

---

## 0. Résumé en dix lignes

1. L'alignement « texte connu sur image » est un sujet ancien (HMM, Viterbi, ancres de mots uniques). La recette de notre pipeline (ancres, remplissage, alignement fin) est celle de **RETAS** (Yalniz et Manmatha, 2011) : elle est solide et documentée.
2. Le CTC donne de bonnes **positions relatives** mais de mauvaises **frontières** (pics étroits, début des caractères retardé). Un remède existe en parole (priors d'étiquettes, ICASSP 2024), jamais testé en OCR à notre connaissance.
3. Les VLM (Gemini en tête) battent les OCR classiques en CER sur l'imprimé ancien (1 à 2 % de CER sur des pages propres), mais **ce chiffre cache** les omissions de colonnes, les boucles de répétition, la modernisation d'orthographe et les substitutions fluides.
4. Aucune étude publiée ne mesure le taux d'omission de Gemini sur journaux denses. C'est un trou de la littérature, et une mesure que nous pouvons produire.
5. Les VLM généralistes sont mauvais pour donner des boîtes de mots ; les modèles spécialisés ajustés (GutenOCR, dots.ocr) ne donnent que des boîtes de lignes ou de blocs. Pas de boîtes au mot fiables en sortie de VLM : le forçage CTC garde donc sa raison d'être.
6. Tableaux : les VLM lisent bien le contenu des cellules, moins bien la structure ; personne n'a publié de méthode pour réconcilier « une rangée = une ligne VLM » avec « un détecteur de lignes coupe en cellules ».
7. Métriques : le CER linéaire est faussé par l'ordre de lecture (14 à 56 % d'erreur apparente sur des pages multicolonnes, alors que le texte est à 80-92 % retrouvé). Des métriques indépendantes de l'ordre existent (FCA, CEV 2026, F1 par morceaux).
8. Rapprocher la structure logique d'un VLM d'un détecteur de mise en page puis des lignes (section 9) : **pas trouvé comme tel** ; des briques voisines existent, aucun résultat comparable publié.
9. Recommandations classées : section 11.

---

## 1. Alignement d'une transcription connue sur l'image

### 1.1 Classiques

| Travail | Idée | Réutilisable pour nous |
|---|---|---|
| Kornfield, Manmatha, Allan, « Text alignment with handwritten documents », DIAL 2004, p. 195-209 (DOI 10.1109/DIAL.2004.1263249, d'après une liste de références) | Aligner les mots d'une ligne manuscrite avec la transcription ; base de référence par les plus grands espaces | Idée de base : la ligne est l'unité, le mot en dessous |
| Rothfeder, Manmatha, Rath, « Aligning Transcripts to Automatically Segmented Handwritten Manuscripts », DIAL 2006 (Springer LNCS, https://link.springer.com/chapter/10.1007/11669487_8) | Aligner un texte sur des lignes/mots segmentés **automatiquement**, donc bruités | Même situation que la nôtre (segmentation imparfaite) |
| Feng et Manmatha, « A hierarchical, HMM-based automatic evaluation of OCR accuracy for a digital library of books », JCDL 2006, p. 109-118 | Alignement hiérarchique par HMM (page, ligne, mot) ; coûteux entre deux ancres éloignées | Montre le coût du « tout en programmation dynamique » |
| **Yalniz et Manmatha, RETAS** (ICDAR 2011 ; titre exact cité de mémoire : « A fast alignment scheme for automatic OCR evaluation of books ») ; page et code : https://ciir.cs.umass.edu/downloads/ocr-evaluation/ | Ancres = mots uniques du livre, retrouvés malgré le bruit OCR ; récursion dans les trous ; alignement d'édition sur de courts morceaux. Choisi pour remplacer l'HMM trop lent | **C'est exactement notre schéma** « ancres, remplissage, caractères ». Le papier valide la robustesse aux erreurs OCR |
| Wemhoener, Yalniz, Manmatha, alignement multi-séquences de plusieurs OCR d'un même livre | Combiner plusieurs lectures | Piste pour le consensus (section 3) |
| Toselli, Romero, Vidal, « Viterbi based alignment between text images and their transcripts », ACL Anthology W07-0902 (2007) ; chapitre « Alignment between Text Images and their Transcripts for Handwritten Documents » (LNCS, 2011, https://link.springer.com/chapter/10.1007/978-3-642-20227-8_2) | Viterbi mot par mot, et niveau ligne quand la page est transcrite sans retours à la ligne | Cas « le texte du VLM n'a pas nos coupures de ligne » |
| Romero, Toselli, Bosch, Sánchez, Vidal, « Automatic alignment of handwritten images and transcripts for training HTR systems », DAS 2018, p. 328-333 | Alignement pour fabriquer des données d'entraînement | Même usage que le nôtre (vérité terrain par alignement) |
| Hassner, Wolf, Dershowitz, « OCR-free transcript alignment », ICDAR 2013 | Aligner sans OCR : rendre la transcription en image synthétique et comparer | Alternative sans lecteur ; non testée sur presse |
| Transkribus Text2Image / Text-Image Matching (https://help.transkribus.org/import-existing-transcriptions-with-text-image-matching ; https://blog.transkribus.org/en/transkribus/docu/text2image/text2image-parameters) | Un modèle HTR lit les lignes ; on cherche la transcription importée par similarité ; seuil de confiance (conseil : 0,01 à 0,05 pour Text2Image ; 0,45 par défaut en ligne pour le nouvel outil) ; options « garder l'ordre », « garder les lignes non appariées » | Mêmes réglages que nos seuils flous ; les lignes non appariées (éléments hors texte principal) sont le défaut signalé |
| passim (Smith, Cordell et al. ; leçon Programming Historian : https://programminghistorian.org/en/lessons/detecting-text-reuse-with-passim) | Détection de réutilisation de texte robuste au bruit OCR | Utile pour retrouver des copies d'un même article dans des numéros différents, pas pour l'alignement ligne à ligne |

### 1.2 Plus récent (2021-2026)

- **Peer, Scius-Bertrand, Fischer**, « CTC Transcription Alignment of the Bullinger Letters: Automatic Improvement of Annotation Quality », ICCV 2025 Workshop VisionDocs ; arXiv:2508.07904. Aligne des transcriptions complètes sur des lignes par programmation dynamique sur les sorties CTC, insère les retours à la ligne (problème des mots coupés en fin de ligne), puis auto-entraînement. Gain de 1,1 point de CER avec PyLaia ; 100 pages corrigées publiées. Constat utile : **un modèle plus faible donne de meilleurs alignements**, ce qui permet une stratégie itérative. Manuscrit du XVIe siècle, pas de la presse, mais c'est le plus proche de notre étape 3.
- **Torras et al.**, « Segmentation-Free Alignment of Arbitrary Symbol Transcripts to Images », ICDAR 2023, LNCS, DOI 10.1007/978-3-031-41498-5_6 (notice OpenAlex ; texte non lu). Et Goio, Torras, Fornés, Megyesi, « Exploring the Alignment of Transcriptions to Images of Encrypted Manuscripts », HistoCrypt 2024 (https://hdl.handle.net/10062/98471) : alignement au niveau du symbole par attention ; l'approche antérieure d'attention retrouve plus de 90 % des symboles (d'après un résumé secondaire).
- **De Gregorio, Capriolo, Marcelli**, « End-to-End Transcript Alignment of 17th Century Manuscripts: The Case of Moccia Code », Journal of Imaging 9(1):17, 2023 (DOI 10.3390/jimaging9010017). Sans apprentissage, projections et chemins A* ; alignement parfait 45 % sur leur manuscrit, 77 à 89 % sur Bentham, Washington, Jefferson. Montre qu'un alignement au mot sans apprentissage plafonne vite.
- **Toselli, Wu, Smith**, « Digital Editions as Distant Supervision for Layout Analysis of Printed Books », ICDAR 2021, arXiv:2112.12703. Utilise le balisage TEI d'éditions numériques (≈ 500 000 pages du Deutsches Textarchiv) comme supervision de mise en page. Principe voisin : une **structure textuelle existante** guide la mise en page.
- « Textline alignment on the image domain », IJDAR 2022, DOI 10.1007/s10032-022-00408-5 (https://link.springer.com/article/10.1007/s10032-022-00408-5) : vu en liste de résultats, résumé non lu.
- **Alignement par VLM** : aucun travail trouvé qui aligne une transcription de VLM sur des lignes détectées pour fabriquer de la vérité terrain (recherche ciblée sans résultat). Le plus proche est la comparaison ligne à ligne contre page entière de Kim et al. (arXiv:2501.11623), qui évalue sans fabriquer de vérité terrain.

**Ce qui manque** : une étude de l'alignement **VLM vers lignes** avec un taux d'erreurs d'alignement chiffré sur de la presse ; un traitement des lignes « fantômes » (détectées mais absentes du texte VLM) et des lignes absentes de la détection.

---

## 2. Alignement forcé CTC pour l'OCR/HTR

### 2.1 Ce qui existe
- Principe : trellis CTC avec blancs facultatifs entre les étiquettes ; documenté en parole (tutoriel NVIDIA https://research.nvidia.com/labs/conv-ai/blogs/2023/2023-08-forced-alignment/ ; CTC-Segmentation, Kürzinger et al., arXiv:2007.09127, qui gère les grands corpus et les écarts texte/audio).
- Boîtes de mots à partir du CTC en HTR : Bullinger (2.2 ci-dessus) travaille au niveau de la ligne. Nous n'avons pas trouvé de papier OCR/HTR évaluant la **précision des frontières de mot** issues d'un alignement CTC contre des boîtes de référence.
- torchaudio fournit `forced_align` mais le signale comme déprécié (docs 2.8, retrait annoncé en 2.9) : prévoir une implémentation propre.
- Je n'ai **pas pu confirmer** que kraken expose un alignement forcé ; à vérifier dans la documentation du dépôt.

### 2.2 Qualité des positions CTC
- Huang et al. (dont Povey, Khudanpur, Watanabe), « Less Peaky and More Accurate CTC Forced Alignment by Label Priors », ICASSP 2024, arXiv:2406.02560 : le CTC concentre sa probabilité sur quelques trames, ce qui est sans gêne pour la reconnaissance mais **raccourcit et décale les durées** ; le début des jetons est retardé. Un prior d'étiquettes réduit de 12 à 40 % les erreurs de frontière de phonème et de mot (Buckeye, TIMIT) ; comparable au Montreal Forced Aligner sur Buckeye. Autre : Chen et al., Interspeech 2023, CTC « non pointu » pour les durées de mots (arXiv:2306.07949).
- Conséquence pour nous : les **centres** de caractère sont fiables, les **bords** ne le sont pas ; plus l'unité modélisée est large (chiffre ou caractère large), pire c'est. Cela rejoint nos constats internes (largeurs apprises, pires cas de quelques pixels).
- Alternatives : attention (Torras et al. ci-dessus), HMM (Toselli/Vidal), OCR-free (Hassner). Aucune n'a été comparée au CTC sur de l'imprimé de presse.

**Nouveauté possible** : transposer à l'OCR les priors d'étiquettes ou une correction de décalage de bord mesurée sur une vérité terrain de boîtes de mots (Reichsanzeiger-GT, section 7), et publier l'erreur de frontière en pixels.

---

## 3. Vérité terrain générée par LLM/VLM

### 3.1 Résultats chiffrés (2024-2026)

| Étude | Données | Résultat |
|---|---|---|
| Greif, Griesshaber, Greif, arXiv:2504.00414 | Annuaires allemands 1754-1870 | Gemini 2.0 Flash : CER normalisé 1,27 % ; contre 3,67 % (Print M1) et 6,31 % (GPT-4o) (d'après un résumé de recherche, à vérifier) ; post-correction multimodale < 1 % |
| Clifford, Polay, Jack, Humphries, Leddy, « Reading the Archive by Machine » (2026-07-10), https://working-papers-in-critical-search.github.io/paper-004-ocr-benchmark/ | 1612-1921 ; dont 8 pages complètes multicolonnes et 600 extraits de journaux | Page complète (Herald 1878) : Chandra 2 0,5 % de CER, Infinity Parser 2 0,6 %, **Gemini 3.5 Flash 1,7 %**, olmOCR 2 16,6 %. Multicolonnes, score par morceaux : Infinity F1 90,2 ; Chandra 83,2 ; **Gemini 82,0 (couverture 99 %, précision 80)** ; olmOCR 44,9 ; GLM-OCR 44,7 |
| Levchenko, LM4DH/RANLP 2025, arXiv:2510.06743 | Russe civil du XVIIIe, 12 modèles | Gemini et Qwen meilleurs que l'OCR classique mais « sur-historicisation » (caractères archaïques ajoutés) ; la post-correction dégrade |
| Kim et al., arXiv:2501.11623 | Tableaux manuscrits belges 1921 | GPT-4o (ligne à ligne) et Claude 3.5 Sonnet (page entière) meilleurs que EasyOCR, Tesseract, TrOCR (CER et BLEU) |
| Crosilla, Klic, Colavizza, arXiv:2503.15195 | Manuscrits 4 langues | Claude 3.5 Sonnet meilleur en zéro-coup ; pas d'avantage net des LLM sur Transkribus ; les LLM corrigent mal leurs propres erreurs |
| Benchmark SSM / Transformers, arXiv:2604.00725 | Journaux antiqua/fraktur, niveau ligne | Gemini entre 7,23 et 10,50 % de CER, derrière les modèles spécialisés (version de Gemini non précisée) |
| METATR, Boillet, Tarride, Kermorvant, arXiv:2605.26712 (mai 2026) | 29 langues | Les modèles propriétaires sont les plus réguliers ; la variation selon l'écriture et la mise en page reste forte |
| olmOCR 2 (arXiv:2510.19817), dots.ocr (arXiv:2512.02498), olmOCR-Bench | Documents modernes surtout | Scores publiés : olmOCR 2 ≈ 82,4, dots.mocr 83,9 ; sous-catégorie « vieux scans » nettement plus basse (48,2 pour dots.mocr, 29,3 pour Mistral OCR), d'après le dépôt dots.ocr |
| Cargnelutti et al. (Boston Public Library), « Institutional Newspapers Pipeline », arXiv:2608.18972 | 1 473 635 scans 1795-1930 | Pipeline modulaire par morceaux (« crops ») avec ordre de lecture : 16,3 milliards de jetons |

Un point de méthode : **les chiffres de CER de page entière dépendent de l'ordre de lecture** (section 6).

### 3.2 Hallucinations, omissions, corrections silencieuses
- Gardella et al., « When Low CER is Not Enough », arXiv:2607.24077 (2026) : documents uruguayens sur microfilm ; les VLM battent l'OCR classique en CER et WER mais présentent trois défauts que ces métriques ne voient pas : **normalisation orthographique, contenu inventé, substitutions sémantiques fluides**, graves sur les noms propres.
- Karamolegkou, Angleraud, Sagot, Clérice, « Reading or Guessing? », arXiv:2605.27750 : sur le grec ancien, les erreurs des VLM restent fluides (substitutions plausibles) alors que l'OCR classique fait du bruit local ; « un texte fluide n'est pas forcément ancré dans l'image ». Les modèles kraken du domaine retrouvent plus de lignes exactes que les VLM.
- Clifford et al. (ci-dessus) : olmOCR 2 invente des noms de lieux plausibles (« Goliath » pour Gotland) ; Gemini lit **trop** (précision 80 contre 87-88).
- Retours de praticiens (non évalués par des pairs) : une lecture VLM de page entière ne rend que 375 mots sur environ 5 900, ou 6 869 mots pour une page de 3 292 (boucle de répétition) ; ce sont des **tickets GitHub** (https://github.com/nealcaren/newspaper-ocr/issues/30), à traiter comme des indices. Même source secondaire : les grandes régions envoyées sans découpage en rectangles de taille raisonnable provoquent des boucles sur la presse du XIXe.
- Beyene et Dancy, « A Survey of OCR Evaluation Methods and Metrics and the Invisibility of Historical Documents », arXiv:2603.25761 (FAccT 2026) : les évaluations ignorent l'effondrement de colonnes, les fautes typographiques et les textes inventés.
- Post-correction : HIPE-OCRepair 2026 (arXiv:2607.08143) conclut qu'il y a un **risque de sur-correction** quand l'entrée est déjà bonne.

### 3.3 Passes multiples et consensus
- Archibald et Martinez, arXiv:2509.09722 : on transcrit plusieurs versions déformées légèrement de la même image avec Gemini 2.0 Flash (marges, flou, grille déformée) et on fusionne par un alignement de type Needleman-Wunsch ; gain d'environ 4 points de précision et un score de confiance ; la déformation en grille sépare le mieux les transcriptions sûres des douteuses. 622 actes de décès de Pennsylvanie.
- ROVER (parole) appliqué à l'HTR : Handwritten Text Recognition from Crowdsourced Annotations, arXiv:2306.10878 compare sélection aléatoire, RASA et ROVER pour fabriquer des étiquettes.
- Limite : une erreur **systématique** commune à toutes les passes n'est pas détectée par le vote.
- **Pas trouvé** : accord Gemini / un second VLM / le CTC comme détecteur d'omission ou de correction silencieuse. C'est ce que votre pipeline peut faire gratuitement : le CTC lit l'image sans modèle de langue fort ; quand il diverge du VLM, l'un des deux a tort.

**Ce qui manque** : taux d'omission/hallucination de Gemini sur journaux denses ; usage d'un lecteur indépendant (CTC kraken) pour détecter les corrections silencieuses du VLM.

---

## 4. VLM avec ancrage spatial

- Qwen2.5-VL (arXiv:2502.13923) : boîtes et points ; performances d'OCR rapportées sur OCRBench v2, pas de précision de boîtes au mot.
- GutenOCR (Heidenreich et al., arXiv:2601.14490, janvier 2026) : Qwen2.5-VL 3B/7B ajustés, lecture, détection et ancrage « lignes et paragraphes » ; score composite 0,40 vers 0,82 sur 10,5 k pages commerciales et scientifiques. Pages modernes ; pas de boîtes au mot.
- DRISHTIKON (arXiv:2506.21316) : Qwen2.5-VL « très en dessous » en ancrage au niveau de la ligne, d'après un résumé de recherche.
- Gemini : un billet de blog (https://simedw.com/2025/07/10/gemini-bounding-boxes/) dit « plutôt bon... mais pas tout à fait » ; un test vendeur sur FUNSD place Gemini 2.5 Pro derrière un OCR commercial. ViDoRe V3 (arXiv:2601.08620) note que Gemini trace des boîtes serrées tandis que Qwen3-VL trace de larges boîtes de sections. Un benchmark académique donne un IoU de 14,4 % pour Gemini 2.5 Pro sur la localisation de preuves alors que la réponse est juste à 84,3 % (arXiv:2602.12203, ExStrucTiny) : **un texte juste n'implique pas une position juste**. Indices seulement, pas de mesure sur du texte historique.
- dots.ocr (Li et al., arXiv:2512.02498) fait mise en page et reconnaissance dans un seul VLM ; le résumé ne dit pas le format des boîtes. FireRed-OCR (arXiv:2603.01840) associe boîtes et texte dans la sortie.
- HisDoc-OCR (Cao et al., Findings ACL 2026, 2026.findings-acl.301) : « injection de mise en page » pour restaurer l'ancrage visuel sur des documents chinois anciens ; résultats chiffrés non lus.
- Praticiens : pour de meilleures boîtes, passer l'image plutôt que le PDF, ou fournir à Gemini des boîtes préalables d'un OCR.

**Lecture pour nous** : garder le VLM pour le **texte**, pas pour la **géométrie** ; à la rigueur lui demander des boîtes de blocs, jamais de mots.

---

## 5. Tableaux historiques

- Nunes et al., « Benchmarking Table Extraction: Multimodal LLMs vs Traditional OCR », XLLM 2025 (https://aclanthology.org/2025.xllm-1.2/) : sur PubTables-1M (moderne), la vision classique garde une petite avance sur la **structure** (GriTS), les modèles multimodaux (GPT-4o, Phi-3 Vision, Granite Vision 3.2) sont bien meilleurs sur le **contenu des cellules**.
- Bäcker-Peral, Meursault, Severen, Philadelphia Fed WP 25-28 / arXiv:2505.11599 (v2 juillet 2026) : tableaux historiques de registres de véhicules ; 95,4 % de cellules exactes, erreurs critiques de structure de 61,4 % à 0,35 %, 96,7 % des cellules numériques exactes, erreur absolue moyenne 0,7 %.
- Clinchant, Déjean, Meunier, Lang, Kleber, DAS 2018, arXiv:1906.11901 : lignes et colonnes de registres manuscrits par CRF ou GCN, F1 89 ; **les rangées sont plus dures que les colonnes**.
- Springer IJDAR 2025, « Tabular context-aware OCR and tabular data reconstruction for historical records » (DOI 10.1007/s10032-025-00543-9) : fournir les cellules voisines au reconnaisseur quand l'écriture déborde de la cellule.
- Transkribus Table Models (https://www.transkribus.org/table-models) : cellules d'abord, lignes de base ensuite, une cellule multiligne reste un enregistrement.
- Presse financière : Origami (Berliner Börsen-Zeitung, CEUR Vol-2723) a un étage tableau simple ; Reichsanzeiger-GT contient 412 régions de tableaux (voir 7). **Aucun jeu de cotes boursières avec structure de cellules trouvé.**
- Guide du bilan historique (arXiv:2204.00052) : mots affectés aux colonnes par leurs coordonnées.

**Ce qui manque** : une méthode pour recoller « une rangée de VLM = une ligne de texte » avec « le détecteur coupe en cellules » ; la solution évidente (fusionner les lignes qui partagent une ordonnée dans un tableau, puis aligner la rangée entière) n'est publiée nulle part, à notre connaissance.

---

## 6. Métriques

- **HIPE-OCRepair 2026** (Ehrmann, Boros, Opitz, Michail, Wagner, Clematide ; arXiv:2607.08143 ; scoreur https://github.com/hipe-eval/HIPE-OCRepair-scorer), lu en texte intégral : métrique principale **cMER**, rapport (substitutions + suppressions + insertions) sur (cela + correspondances), borné entre 0 et 1. Normalisation avant score : retrait des césures douces suivies de saut de ligne, sauts de ligne en espaces, **minuscules, ponctuation remplacée par des espaces**, espaces fusionnés ; **sensible aux accents**. Agrégation micro (somme des comptes) et macro (moyenne par unité) ; score de préférence = signe (cMER avant moins cMER après) par unité ; intervalles de confiance bootstrap (10 000 tirages). Résultat : BnF-Mistral (Mistral Small 3, 24 B, préentraîné sur de l'historique BnF) premier partout ; français cMER 0,0042 contre 0,0176 sans correction (icdar2017 fr : 0,0040 contre 0,0184 ; impresso-snippets fr : 0,0044 contre 0,0169). Cette normalisation est une base pour nous. **Le nom « OCRepair 2025 » mentionné dans la demande est en fait HIPE-OCRepair 2026** ; je n'ai pas trouvé de papier 2025 de ce nom.
- **Ordre de lecture** : *Flexible Character Accuracy* (Clausner, Pletschacher, Antonacopoulos, Pattern Recognition Letters 2020, ScienceDirect S0167865520300416 ; auteurs cités de mémoire) ; l'évaluation OCR-D le mentionne mais ne l'utilise pas encore ; PRImA, sac de mots ; **Character Error Vector**, Bourne, Simbeye, Nockels, arXiv:2604.06160 (avril 2026) : sac de caractères, découpe l'erreur en analyse de la page, OCR et interaction, implémentation SpACER (CER spatial) ; sur journaux dégradés, les modèles de bout en bout font pire que les chaînes classiques ; **F1 par morceaux** de Clifford et al. (couverture, précision, rappel, indépendant de l'ordre). Le CER linéaire va de 14 à 56 % sur les mêmes pages à cause de la seule sérialisation.
- Sur les entités : « Reading Order Independent Metrics for Information Extraction in Handwritten Documents », arXiv:2404.18664 (ECER/EWER).
- Métriques de défaut propres aux VLM : HCPR et AIR de Levchenko (conservation des caractères historiques, insertions archaïques) ; les trois défauts de Gardella et al. (aucun n'est une métrique officielle).

**Ce qui manque** : une métrique de **fidélité de la vérité terrain générée** qui sépare : omissions, ajouts, modernisation, erreurs de lecture, erreurs de position ; et une mesure de position (boîte au mot) indépendante du texte.

---

## 7. Projets et corpus comparables

- **Reichsanzeiger-GT** (Univ. Mannheim, Data in Brief, 2024 ; PMC10980999 ; https://madata.bib.uni-mannheim.de/445) : 101 pages 1820-1939, 65 563 régions de texte, **412 régions de tableaux**, 119 429 lignes, 490 679 mots ; Transkribus pour la mise en page, Tesseract pour les lignes, deux corrections humaines par page ; deux variantes PAGE (tableaux gardés ou convertis en texte). Seul corpus de presse avec boîtes au mot et tableaux que nous avons trouvé : bon pour mesurer nos boîtes. Allemand, pas français.
- **Chronicling Germany** (Schultze et al., arXiv:2401.16845) : 693 pages 1852-1924, mise en page et OCR ; les erreurs de mise en page coupent les lignes en classes différentes, ce qui fausse l'appariement à l'évaluation.
- **NewsEye / HIPE-2022** (Ehrmann, Romanello, Doucet, Clematide ; https://zenodo.org/records/6463040, https://hipe-eval.github.io/HIPE-2022/) : journaux fr, de, fi, sv ; vérité terrain de **NER**, pas d'OCR pur.
- **impresso** : jeux impresso-snippets (nouveau, 50 paragraphes par langue en fr, de, en) et impresso-nzz (pages de la NZZ, ABBYY FineReader 11) dans HIPE-OCRepair 2026 ; https://github.com/impresso/NZZ-black-letter-ground-truth.
- **American Stories** (Dell et al., arXiv:2308.12477) : mise en page, classification de lisibilité, OCR personnalisé et chaînage de boîtes sur près de 20 millions de scans de Chronicling America ; les chiffres annoncés (400 millions ou plus d'un milliard d'articles) divergent selon les sources, non réconciliés.
- **BnF/Gallica** : jeux de presse corrigée manuellement dont NewsEye et IMPACT, formats ALTO et PAGE (https://api.bnf.fr/fr/ocr-corrige-de-documents-de-presse-de-gallica) ; texte corrigé et OCR aligné (https://api.bnf.fr/fr/texte-corrige-et-ocr-de-documents-de-gallica) ; documents de presse Europeana Newspapers (https://api.bnf.fr/fr/documents-de-presse-numerises-en-mode-ocr-du-projet-europeana-newspapers).
- **PERO OCR** (Kodym, Hradiš, arXiv:2102.11838 ; https://github.com/DCGM/pero-ocr) : chaîne complète avec modèle pour la presse tchèque ; critère de ligne correcte : chevauchement, moins de 15 % de différence, même position dans l'ordre.
- **Compétitions ICDAR** : pas trouvé de compétition ICDAR 2023-2025 d'OCR de presse. Existent : HIPE-OCRepair 2026 (post-correction) ; cartes historiques 2024 et 2025 (https://link.springer.com/chapter/10.1007/978-3-032-04630-7_33) ; ICDAR 2025 FEST (lignes manuscrites anciennes, arXiv:2509.12965). Séparation d'articles de presse : Ar-Q-Former (ICDAR 2025, https://link.springer.com/chapter/10.1007/978-3-032-04624-6_28), STRAS (https://link.springer.com/article/10.1007/s00799-025-00437-5). Ordre de lecture arménien avec LLM : Vidal-Gorène et al., arXiv:2607.00596 (ICPR 2026), 66 pages, jusqu'à 76 % d'erreurs d'ordre en moins que la meilleure base géométrique.
- Organisation du travail à l'échelle : « Institutional Newspapers Pipeline » (ci-dessus), qui montre qu'on traite la presse par petits morceaux.

---

## 8. Chaînes qui rapprochent déjà texte, mise en page et lignes

- **Mocaër et al., « Towards Hierarchical Structure Understanding of Newspaper Images »**, atelier ICDAR 2026 HIP, arXiv:2607.15082 : chaîne modulaire (YOLO pour la mise en page, LayoutReader pour l'ordre, algorithme de séparation d'articles) contre le transformeur de bout en bout Tiramisu ; nouveau jeu sur La Liberté. Résumé sans chiffres lus.
- Gutehrlé et Atanassova, « Processing the structure of documents: Logical Layout Analysis of historical newspapers in French », Journal of Data Mining & Digital Humanities (NLP4DH), 2022, arXiv:2202.08125 : structure logique à partir d'ALTO sur de la presse française ; règles contre RIPPER et Gradient Boosting, **les règles gagnent** (rappel plus élevé).
- Coût de la mise en page : DocLayout-YOLO (arXiv:2410.12628 : 70,3 % de mAP sur D4LA, 79,7 % sur DocLayNet, 85,5 images/s) ; PP-DocLayout (arXiv:2503.17213 : 23 classes dont journaux ; PP-DocLayout-M 75,2 % de mAP@0,5, -L 90,4 %). Sur la presse arménienne, DocLayout-YOLO avec préentraînement synthétique dépasse YOLOv11x de 1 à 2 points de mAP@50 (arXiv:2607.00596).

---

## 9. Section ajoutée : rapprocher la structure logique d'un VLM d'un détecteur de mise en page, puis des lignes kraken (du grossier au fin)

**Question** : un VLM rend du Markdown ou de l'OLR (titres, paragraphes, tableaux en rangées et colonnes, parfois des boîtes approximatives). Peut-on rapprocher cette structure des régions d'un détecteur de mise en page (YOLO presse, DocLayout, PP-DocLayout), puis des lignes kraken, pour guider l'alignement à chaque niveau (bloc, ligne, mot) ?

**Réponse : pas fait comme tel. Aucun travail trouvé qui apparie le Markdown/OLR d'un VLM aux régions d'un détecteur puis aux lignes pour fabriquer de la vérité terrain, et aucun résultat chiffré comparable n'existe.** Ce n'est pas une preuve d'absence : les recherches web ciblées ont donné zéro résultat direct, et seul un résumé a été lu pour chaque voisin ci-dessous.

### Les briques voisines existantes
1. **Coarse-to-fine côté modèle** : MinerU2.5, Dolphin, MonkeyOCR détectent la mise en page sur une image réduite, puis lisent chaque région découpée en haute résolution (décrit dans la revue de Beyond the Grid, arXiv:2603.01666 ; je n'ai pas vérifié les trois systèmes un par un). Ici la structure est interne au modèle : il n'y a pas de « rapprochement a posteriori ».
2. **Boîtes et texte dans la même sortie** : FireRed-OCR (arXiv:2603.01840), dots.ocr (arXiv:2512.02498), GutenOCR (arXiv:2601.14490). Le rapprochement est fait par le modèle ; on ne mesure pas l'exactitude des boîtes par rapport à une vérité terrain historique.
3. **Chaînes modulaires presse** : Mocaër et al. (YOLO + ordre de lecture + séparation d'articles), Vidal-Gorène et al. (zones sémantiques + LLM pour l'ordre), Gutehrlé et Atanassova (règles sur ALTO). Elles travaillent de la **mise en page vers le texte** (elles ordonnent des zones), pas en alignant un texte VLM existant.
4. **Supervision par la structure d'un texte existant** : Toselli, Wu, Smith (2021) projettent le balisage d'éditions TEI sur les pages. C'est le même principe — une structure textuelle guide la détection — mais avec une édition numérique et non un VLM.
5. **Appariement texte-lignes avec seuils par bloc** : Transkribus Text2Image (seuil « région » pour apparier d'abord par bloc, puis par ligne). C'est un alignement du grossier au fin, mais avec le texte de l'HTR comme intermédiaire et sans structure logique.
6. **Tableaux : lignes puis cellules** : Clinchant et al. étiquettent chaque ligne par sa position dans la cellule (début, milieu, fin, seule, hors) puis regroupent en rangées ; Transkribus fait cellules puis lignes de base. Ce sont les deux seules méthodes publiées proches de notre problème « une rangée coupée en cellules ».
7. **Évaluation indépendante de l'ordre** : F1 par morceaux (Clifford et al.) et CEV (Bourne et al.) retrouvent chaque passage où qu'il soit dans la sortie, donc **déjà adaptés à un appariement région-bloc sans ordre**.

### Résultats chiffrés disponibles (très partiels)
- Ordre de lecture : jusqu'à 76 % d'erreurs en moins avec zones sémantiques + LLM contre la meilleure base géométrique (66 pages arméniennes).
- Détecteurs de mise en page : 75 à 90 % de mAP@0,5 pour PP-DocLayout, 1 à 2 points d'écart entre DocLayout-YOLO et YOLOv11x ajusté sur la presse arménienne ; **raretés mal détectées** (marginalia, métadonnées).
- Aucun chiffre sur « quelle part des blocs Markdown du VLM peut être appariée à une région détectée », ni sur l'effet d'un appariement par bloc sur la précision de l'alignement ligne.

### Ce que cela suggère pour votre pipeline (hypothèses à tester, pas des résultats publiés)
1. **Niveau 1, bloc** : apparier chaque bloc VLM (titre, paragraphe, tableau) à une région détectée par similarité de texte **bag-of-characters** (robuste à l'ordre) pondérée par la proximité des boîtes approximatives quand elles existent ; c'est un petit problème d'affectation (Hongrois) avec un coût mixte texte/géométrie. Les régions sans bloc et les blocs sans région sont signalés (ce sont des omissions du VLM ou des fausses détections).
2. **Niveau 2, ligne** : dans chaque paire (bloc, région), n'aligner que les lignes kraken de la région avec le texte du bloc. Cela réduit la fenêtre de recherche floue et évite les alignements croisés entre colonnes ; cela traite aussi l'ordre de lecture (celui du bloc, pas celui de la page).
3. **Niveau 3, tableau** : un bloc « tableau » donne un nombre de rangées ; regrouper les lignes kraken de la région par ordonnée en rangées (méthode de Clinchant et al. pour les étiquettes de position), et aligner chaque rangée VLM sur la **concaténation** des cellules lues, avant d'éclater en cellules. Cette étape n'est pas publiée telle quelle.
4. **Niveau 4, mot** : alignement forcé CTC au sein de la ligne (section 2).
5. **Contrôle d'erreur à chaque niveau** : un bloc dont la similarité globale est basse est mis de côté plutôt qu'aligné de force ; mesurer la proportion de caractères VLM placés par niveau.

**Risques** : les régions fusionnées ou coupées du détecteur (déjà vu : Chronicling Germany signale des lignes coupées en classes différentes), les blocs VLM qui fusionnent deux colonnes ou qui sautent un encadré, et l'absence de détecteur entraîné sur la presse française (les modèles cités sont modernes ou entraînés ailleurs).

**Nouveauté possible** : c'est un trou net. Une publication « appariement hiérarchique Markdown du VLM vers régions vers lignes vers mots, avec taux de placement par niveau » serait nouvelle, à condition de la comparer à l'alignement plat actuel.

---

## 10. Ce qui n'a pas pu être vérifié (honnêteté)

- Texte intégral lu : seulement arXiv:2607.08143 (HIPE-OCRepair). Pour tous les autres, résumé ou page de description.
- Titre exact de RETAS (ICDAR 2011) cité de mémoire ; la page https://ciir.cs.umass.edu/downloads/ocr-evaluation/ confirme la méthode et le code.
- Auteurs de Flexible Character Accuracy (Clausner et al.) cités de mémoire ; titre et revue confirmés par la recherche.
- Chiffres de Greif et al. (1,27 / 3,67 / 6,31 %) : issus d'un résumé de moteur de recherche, non revus dans le papier.
- Ni les papiers « Textline alignment on the image domain » (IJDAR 2022) ni HisDoc-OCR (chiffres) ni Torras et al. 2023 ni Mocaër et al. 2026 n'ont été lus au-delà du résumé.
- Aucune confirmation que kraken possède un alignement forcé intégré.
- Je n'ai **rien trouvé** sur : Bluche (alignement), Ströbel (alignement de transcriptions de presse), Feng-Manmatha 2006 (résumé), eScriptorium (alignement), OCR-D `ocrd-align`, Europeana Newspapers en détail. Ces pistes sont donc non couvertes, pas absentes de la littérature.
- Le nom du jeu de données de Mocaër et al. contient le nom d'un système tiers ; par consigne du projet, nous ne le reprenons pas ; nous le désignons par « jeu La Liberté (Mocaër et al.) ».
- Les identifiants arXiv 26xx datent de 2026 ; ils se sont ouverts normalement lors de la recherche mais je n'ai pas pu recouper leur existence autrement.

---

## 11. Recommandations classées pour le pipeline

1. **Ajouter un contrôle indépendant des omissions et corrections silencieuses du VLM** : comparer la transcription VLM au CTC kraken ligne par ligne (désaccord = suspect), et signaler les lignes détectées sans texte VLM et les blocs VLM sans ligne. Rien de publié ne le fait ; c'est le plus gros gain de fiabilité et c'est peu coûteux. Quantifier d'abord les taux d'omission de Gemini sur votre presse (trou de la littérature).
2. **Aligner du grossier au fin (section 9)** : blocs vers régions du détecteur, puis lignes, puis mots. Mesurer la part de caractères placés à chaque niveau et la comparer à l'alignement plat actuel. Nouveauté publiable.
3. **Traiter les tableaux par rangée** : regrouper les lignes kraken par ordonnée, aligner la rangée VLM sur la rangée détectée, éclater ensuite en cellules. S'appuyer sur Clinchant et al. (étiquettes de position) pour la détection des rangées. Valider sur les 412 tableaux de Reichsanzeiger-GT.
4. **Évaluer avec des métriques indépendantes de l'ordre** : F1 par morceaux, CEV, FCA, en plus d'un CER normalisé à la manière de cMER (minuscules, ponctuation, césures) mais **avec** une variante stricte (accents, chiffres) pour la presse financière. Toujours reporter l'ordre de lecture séparément.
5. **Mesurer l'erreur de frontière du CTC en pixels** sur Reichsanzeiger-GT (boîtes au mot) et tester une correction de décalage ou un prior d'étiquettes (ICASSP 2024). Utiliser les centres de caractère plutôt que les bords quand c'est possible.
6. **Plusieurs passes du VLM avec déformations légères** (Archibald et Martinez) pour obtenir un score de confiance par segment ; envoyer des morceaux de taille raisonnable (pas de très grandes régions) pour éviter les boucles de répétition ; traiter les segments instables comme « à revoir » plutôt que de les aligner de force.
7. **Chiffres, fractions, cotes** : ne pas se fier au CTC ; croiser la lecture VLM de chaque cellule numérique avec une deuxième lecture (autre passe ou autre modèle) et exiger l'accord avant d'inscrire la valeur ; les cotes boursières n'ont aucun jeu public, donc constituer un petit jeu de contrôle manuel.
8. **Seuils d'abstention** : s'inspirer de Text2Image (seuil de confiance, option de garder les lignes non appariées) et de Bullinger (un modèle plus faible aligne mieux ; itérer) : publier la vérité terrain avec un indicateur par ligne, jamais « tout aligné ».
9. **Détecteur de mise en page adapté à la presse française** : essayer DocLayout-YOLO ou PP-DocLayout en zéro-coup comme garde-fou, comparer à un YOLO ajusté (écart de 1 à 2 points seulement sur la presse arménienne) avant d'investir dans l'ajustement.
10. **Publier** : (a) taux d'omission/corrections silencieuses de Gemini sur journaux français, (b) appariement hiérarchique, (c) erreur de frontière CTC en OCR. Chacun est une lacune identifiée par cette revue.

---

## Références clés (liens)

- RETAS : https://ciir.cs.umass.edu/downloads/ocr-evaluation/
- Bullinger CTC : https://arxiv.org/abs/2508.07904
- Label priors CTC : https://arxiv.org/abs/2406.02560
- HIPE-OCRepair 2026 : https://arxiv.org/abs/2607.08143 ; scoreur https://github.com/hipe-eval/HIPE-OCRepair-scorer
- Reading the Archive by Machine : https://working-papers-in-critical-search.github.io/paper-004-ocr-benchmark/
- Character Error Vector : https://arxiv.org/abs/2604.06160
- Hallucinations uruguayennes : https://arxiv.org/abs/2607.24077
- Reading or Guessing : https://arxiv.org/abs/2605.27750
- Levchenko : https://arxiv.org/abs/2510.06743
- Greif et al. : https://arxiv.org/abs/2504.00414
- Archibald et Martinez : https://arxiv.org/abs/2509.09722
- GutenOCR : https://arxiv.org/abs/2601.14490 ; dots.ocr : https://arxiv.org/abs/2512.02498
- Tableaux : https://aclanthology.org/2025.xllm-1.2/ ; https://arxiv.org/abs/2505.11599 ; https://arxiv.org/abs/1906.11901
- Reichsanzeiger-GT : https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10980999/
- Hiérarchie de presse : https://arxiv.org/abs/2607.15082 ; ordre de lecture arménien : https://arxiv.org/abs/2607.00596 ; logique du français : https://arxiv.org/abs/2202.08125
- DocLayout-YOLO : https://arxiv.org/abs/2410.12628 ; PP-DocLayout : https://arxiv.org/abs/2503.17213
- Survey évaluation OCR historique : https://arxiv.org/abs/2603.25761 ; METATR : https://arxiv.org/abs/2605.26712
