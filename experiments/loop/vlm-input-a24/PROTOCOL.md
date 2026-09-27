# A24 — ablation d'entrée VLM sur réserve consommée

Diagnostic postérieur, sans valeur de validation indépendante. Les 16 IDs A22
et leur référence ont déjà été ouverts et scorés. Aucun paramètre ne sera retenu
comme gagnant sans nouvelle réserve.

Une seule tâche gpt-6-sol lit, pour chaque ID, un composite construit sans texte
de référence : (1) page entière avec la ligne encadrée, (2) voisinage vertical
de trois hauteurs agrandi 2x, (3) ligne avec marge agrandie 4x. Le prompt et les
IDs restent identiques dans leur intention à A22. La sortie est comparée à la
lecture A22 (crop natif + version non masquée) en CER strict et selon le profil
documenté `glyph_decomposition_v1`.

Cette expérience teste si le contexte et l'échelle d'entrée expliquent une part
de l'écart avec les résultats Claude/Gemini rapportés par l'utilisateur. Elle ne
compare pas directement les fournisseurs, puisque leurs sorties et réglages
exacts ne sont pas disponibles ici.

