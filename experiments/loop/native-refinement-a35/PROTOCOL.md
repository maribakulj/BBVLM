# A35 — retirer la transcription oracle du raffinement

Diagnostic sur A28 et A34 consommés, aucun réglage et aucune nouvelle validation
indépendante. Défaut à isoler : A32/A34 dépendaient du texte et du nombre de mots
de référence, ce qui surestime l'applicabilité aux prédictions réelles.

Reprendre les boîtes PERO natives et leurs tokens réellement reconnus. Comparer
les boîtes inchangées, le seuillage Otsu et A32 corps+satellites inchangé. Ne
modifier ni texte ni cardinalité ni ordre. Lignes source et baselines synthétiques
restent oracle. Zéro nouvelle inférence : le coût historique du recognizer reste
explicitement comptabilisé.

Utiliser le même appariement géométrique hongrois pour toutes les variantes,
y compris le comparateur A32 au texte oracle. Fournir aussi les deltas avec
l'appariement du PERO natif fixé, pour séparer raffinement et réappariement.
Rapporter les scores conjoints texte exact + IoU sous la convention de glyphes
historique documentée; ce diagnostic n'est pas le CER opérationnel Gallica.

Garder tous les mots reconnus, y compris faux tokens, et les lignes OCR vides.
Ne pas compenser une omission par un mot de référence. Hacher les entrées et
vérifier leur intégrité après exécution. Aucun gate final ne passe avec ce test.
