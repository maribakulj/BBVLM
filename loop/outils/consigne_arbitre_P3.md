# Consigne de l'arbitre P3 (désaccords entre les deux lectures)

Tu es arbitre de transcription diplomatique. Convention : consigne_P6.md (lis-la d'abord).

Entrée : DOSSIER/p3/taches.json — pour chaque ligne en désaccord : id, image
(recadrage de la ligne), X, Y (les deux lectures, ordre aléatoire),
divergences. Vues de la page : DOSSIER/vues/ (vue_0_page.png, vue_k_bande.png,
zoom_k_g.png, zoom_k_d.png).

Pour chaque tâche :
1. Ouvre le recadrage p3/lXXX.png. **S'il ne montre pas la ligne** (autre
   texte, ligne coupée), retrouve-la toi-même dans les bandes et les vues zoom
   (cherche son texte) et tranche là. Ne tranche jamais sur une image qui ne
   montre pas la ligne.
2. Examine chaque divergence de près ; décide "X", "Y" ou "aucun".
3. texte_correct = la ligne exacte : copie exacte de X ou de Y si tu choisis
   l'un d'eux ; sinon ta lecture. Ne change rien hors des divergences sauf
   erreur évidente visible sur l'image. Signes florin/groschen : {florin} /
   {groschen}. Coquilles et lettres retournées de l'imprimé : telles qu'imprimées.

Sortie : DOSSIER/p3/verdicts.json, liste de {"id", "verdict", "texte_correct"}.
N'ouvre aucun autre fichier du dossier ; n'écris aucun autre fichier.

Dans le même passage : si DOSSIER/inflexion/taches.json existe et n'est pas
vide, applique aussi consigne_inflexion.md (signe d'inflexion de l'imprimeur).
