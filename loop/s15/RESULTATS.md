# S15a — Orli (L35) comme source de lignes manquées par kraken (30/09) — REJETÉE

Protocole : orli_base (zenodo 10.5281/zenodo.20558179), kraken 7.0.3, torch 2.12 CPU, bf16-mixed, polygonize ; venv séparé (venvo) pour ne pas toucher venvk. Mesure : rappel des lignes VT (IoU boîte ≥ 0,5) et récupération des lignes VT absentes de kraken_crit2 (lignes de la chaîne).

| page | lignes VT | kraken (chaîne) | Orli | lignes Orli produites | ligne manquée par kraken : meilleur IoU Orli | temps |
|---|---|---|---|---|---|---|
| euanaua/143 | 22 | 21 | 15 | 43 | « Am I. Sontag » 0,29 | 132 s |
| DasWeL/71 | 26 | 25 | 19 | 90 | « I ĳ » 0,36 | 139 s |

- Orli sur-segmente (lignes coupées aux blancs des vers et des listes), rappel inférieur à kraken, et ne récupère aucune des deux lignes manquées. Rejetée pour cet usage ; pas étendue aux 4 autres pages.
- Constat utile (euanaua) : la ligne « Am I. Sontag » n'est pas absente mais mal cadrée : titre en grandes capitales ornées (encre de y = 552 à 693) ; kraken la coupe en deux morceaux [80,615,570,686] + [638,646,831,677] qui ne couvrent que le corps des lettres ; leur union aurait IoU ≈ 0,47 avec la VT. Piste S15b : union des morceaux kraken d'une même ligne lue + extension verticale à l'encre connexe.

## Classement des 16 lignes VT sans ligne kraken (IoU < 0,5), après A05
- morceaux dont l'union suffirait (IoU union ≥ 0,5) : 5 — geomeikud/37 « ij. Treer » (0,95), « iij. Mentz » (0,94), 688357687 « Bk. Ater Ch. (F) » (0,86), 852691769 titres verticaux « Clas I. … », « Cla. II. … » (0,86, 0,81) ;
- ligne kraken trop haute (deux lignes réunies) : 5 — durrgeda « JENA/ gedrut… » (0,26), 852691769 « 2. — 6. » (0,28), « 4. — 5. » (0,48), herbdulc « Vita optabi- » (0,27), goclprop « Exetc. 107. di. 2. » (0,49) ;
- numéro de liste à gauche manqué : 2 — geomeikud/34 « j. Jsop », geomeikud/37 « i. Cllen » ;
- absentes : 2 — DasWeL « I ĳ », durrgeda « Hꝛn. Friedri » (grand titre) ; titre mal cadré : 1 — euanaua « Am I. Sontag ».

## S16 — ancre CATMuS au lieu de Tesseract pour S11 : rejetée sans mesure CRITERE
Cause de l'échec de S11 sur geomeikud/37 : Tesseract lit « ij. » → « Li. », « Treer » → « Îyeey ». CATMuS (lecture W05 déjà en cache) lit plus mal encore ces grands caractères : « ti. », « Crter », « tti. », « Dteattg » (Mentz). Aucune ancre OCR fiable sur ces lignes → piste S17 sans OCR : boîte kraken sans ligne lue appariée, dans la bande d'une boîte appariée → fusion.

## S17 / S17b — fusion des boîtes kraken orphelines de bande : REJETÉES
- S17 (sans OCR) : geomeikud/37 3 → 1 ligne en échec, mais buchdas/27 1 → 2 (annotations manuscrites de marge rattachées aux lignes imprimées).
- S17b (+ encre de même nature : p10 de l'orpheline ≤ p10 de la voisine + 30 ; manuscrit ≈ 107, imprimé 32-39) : petits lots sans recul, mais O07-O17 (23/44 pages mesurées) hackherz 2 → 3, 852691769 6 → 10. Mesure interrompue.
- Bilan : une règle réglée sur deux pages se casse sur d'autres. Fin des règles géométriques ponctuelles (JOURNAL 30/09 17h10 : changement de paradigme).

## SR — segmentation par reconnaissance guidée par le texte lu (L36) — protocole pré-enregistré (30/09 17h25)
- Candidates : lignes de la chaîne (après S08…S09) + unions de 2-3 boîtes voisines d'une même bande sans boîte intercalée. Score = perte CTC (W05, CATMuS-Print) de la ligne lue sur la candidate / (nb signes + 1). Affectation hongroise lignes lues × candidates, paires ≤ τ = 4,5 (valeur générique, non réglée), conflits de recouvrement résolus en gardant la meilleure paire ; lignes kraken non recouvertes gardées.
- Essai de faisabilité : « iij. Mentz » 2,51 sur l'union contre 7,87 / 11,5 sur les morceaux (lecture libre CATMuS : « Dteattg ») ; buchdas/27 : ligne imprimée seule préférée à l'union avec l'annotation manuscrite (1,21 / 1,26 ; 0,38 / 3,52).
- Jeu tenu à l'écart dès maintenant : O23-O25 (12 pages : crit23/24/25) ; dev : O07-O18 (48 pages : crit2/crit18). Critère d'adoption : CRITERE dev non en recul, aucune page dev +1 ligne en échec ; résultat sur l'écart rapporté tel quel.
- SR v1 (hongrois + interdictions itératives) : geomeikud/37 3 → 1, mais herrleyc/44 (×2 lots) et AmmoLIBR/110 0 → 1 ligne en échec. Cause (herrleyc) : la résolution des conflits interdisait des paires de façon permanente et laissait tomber la manchette « Syrach. 15. » alors que les scores étaient justes (1,73 sur son morceau ; ligne de texte 0,93 sur sa boîte, 1,77 sur l'union). Défaut d'algorithme, pas de score.
- SR v2 : choix glouton global (paires triées par score, ligne libre et candidate sans recouvrement avec les prises). Vérifié : herrleyc et AmmoLIBR inchangés, geomeikud corrigé. Mesure complète relancée.
- SR v2 : écart (O23-O25) inchangé, geomeikud/37 3 → 1, mais herrleyc/41 0 → 1 : une petite ligne kraken (779,266,926,308) qui chevauchait une ligne choisie était retirée par la règle « lignes non recouvertes gardées ».
- SR v3 : toutes les lignes kraken sont gardées ; seuls les morceaux contenus dans une union choisie sont remplacés par elle. Vérifié sur herrleyc/41 (inchangé) et geomeikud/37 (corrigé). Mesure complète relancée.
- **SR v3 — résultat** (etat_sr/) : dev (O07-O18, 48 pages) 32/48 → 32/48, écart (O23-O25, 12 pages) 8/12 → 8/12 : CRITERE 40/60 inchangé ; aucune page en recul ; geomeikud/37 3 → 1 ligne en échec ; précision : 852691769 ≤0,5c 99,38 → 100 %, pire 0,61 → 0,47 c ; herbdulc pire 0,92 → 0,38 c ; caladr IoU méd 0,960 → 0,965. Critère d'adoption tenu → **SR v3 adoptée** (BBVLM_SR=1 par défaut). Scissions (BBVLM_SR_SCINDE) : non mesurées.

## T02 — perte CTC (W05) comme arbitre des blancs d'une ligne lue : NÉGATIF (essai, 30/09)
Lignes de l'audit A04 (relecteurs aveugles = vérité) : ligne kraken appariée à la VT, perte CTC de notre lecture contre la même lecture avec les blancs de la VT (reblanc). Cas nets : « vff.xxxviij. jar » (VT) préféré ✓ ; « Krieges⸗ und » ✓ ; mais « ihmviel » (soudé, faux) préféré à « ihm viel » (1,33 contre 1,45) ✗ ; plusieurs variantes mal construites quand les glyphes VT diffèrent des nôtres (reblanc déporte les blancs). CATMuS distingue mal l'espace du blanc CTC : la perte n'est pas un arbitre fiable des soudures. Abandonné.
