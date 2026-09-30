# W05 — alignement forcé CTC (Viterbi) du texte lu sur les émissions kraken CATMuS

Figé le 2026-09-30 (12h24 Paris). Déclencheur : question de l'utilisateur (conversation sur Hans/Saknussemm : le CTC doit servir de localisateur par alignement forcé, pas de second OCR dont on rapproche le texte).
Constats avant protocole :
- W04 (rejetée) n'était **pas** un alignement forcé : src/boxers/ctc.py décode le CTC puis rapproche le texte par SequenceMatcher. W04 ne dit rien de l'alignement forcé.
- kraken 7.1.1, align.forced_align : `model.outputs` est déjà un softmax (models.py l.115) et le code lui réapplique log_softmax → émissions quasi plates ; son treillis (tutoriel wav2vec) n'autorise qu'une trame par caractère. Explication plausible de la « géométrie effondrée » rapportée par Hans (non vérifiée sur leur modèle).
- Diagnostic sur 8 lignes de BrenBreu/72 (texte VT imposé, frontières contre les mots VT, sans recalage) : 51/51 à ≤ 0,5 c, pire 0,47 c (c = 0,45 × hauteur de ligne, mesure de diagnostic, pas CRITERE).
Implémentation : outils/w05.py (Viterbi CTC standard 2L+1 états sur log(probas) ; frontière = milieu entre dernière trame du mot k et première du mot k+1 ; recalage au blanc d'encre ≤ 3 px ; caractères non codés par CATMuS : repli ſ→s, ꝛ→r, etc.).
Deux mesures :
1. Géométrie isolée (diagnostic, VT imposée, 60 pages) : part des frontières ≤ 0,5 c, pire par page.
2. Chaîne (décisive) : BBVLM_W05=tout (remplace W02 en Fraktur, ajoute en romain) puis variantes fraktur / romain ; CRITERE crit2/18/23/24/25 MODE=chaine2.
Adoption : CRITERE total ≥ 33/60 (actuel 31) sans recul de lot ; sinon adoption partielle (fraktur ou romain) seulement si elle-même ≥ 32/60 sans recul. Pire page : aucune page ne passe de ≤ 3 c à > 3 c.
