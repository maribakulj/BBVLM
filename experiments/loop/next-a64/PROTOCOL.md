# A64 — projection HIPE-OCRepair sur l'évaluation BnL gelée

Cette expérience ne produit aucune nouvelle transcription et ne règle aucun
paramètre. Elle rescrore les seize blocs indépendants A54, déjà gelés, avec la
normalisation et le Match Error Rate (MER) publiés par le scorer
HIPE-OCRepair 0.9.9. Les textes comparés sont PERO, Luna brut, Luna avec garde
locale et Luna avec abstention sur incertitude. Les références XML restent
immuables.

Source primaire réellement lue :
`hipe-eval/HIPE-OCRepair-scorer`, commit
`d1e76e447629ea9cf8dead32ae3c44b0d48d77b3`, fichiers `ocrepair_eval.py`,
`pyproject.toml` et README. La normalisation exacte met en minuscules, applique
les substitutions historiques déclarées, supprime les fins de ligne DTA
`—\n`/`¬\n`, remplace tout caractère hors `\w` par un espace, remplace `_`,
puis compacte les espaces. Le cMER est `(S+D+I)/(H+S+D+I)`. Le score de
préférence vaut +1/0/-1 par bloc selon que la correction améliore/égale/dégrade
PERO. Le code local doit être testé contre `jiwer.process_characters` avant la
mesure ; cette validation d'implémentation ne valide pas les références.

La projection HIPE est ajoutée comme quatrième vue, sans remplacer
`strict_nfc_diplomatic`, `search_v1` ou `lexical_alnum`. Un zéro HIPE ne serait
pas un zéro diplomatique : casse, ponctuation et certains caractères
historiques sont neutralisés. Rapporter micro-cMER, nombre de blocs améliorés,
égaux, dégradés, lignes exactes et différences avec les trois vues existantes.

Branche Claude inspectée avant hypothèse : head
`76056c5c1957e0de4232f0aef1f6cbc7f2893402`, JOURNAL I01 blob
`ba685e9b4c870e245d1d201381986178660abb4c`, inchangés depuis A63. La règle
I01 reste du développement en attente d'O13 et ne concerne pas cette métrique.

Limites pré-enregistrées : A54 a déjà été consommé ; aucune preuve nouvelle de
généralisation, géométrie, OLR ou vérité terrain parfaite. La référence BnL est
annoncée double-saisie mais contient des erreurs probables. L'objectif est de
quantifier l'effet des conventions et les régressions par item, pas d'obtenir
artificiellement 0 %.
