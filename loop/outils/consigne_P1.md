# Consigne de transcription diplomatique (OCR-D niveau 2)

Tu transcris une page imprimée ancienne (allemand Fraktur, latin, français, bas-allemand…), 1500-1830.

Vues fournies : vue_0_page.png (page entière réduite, pour la mise en page) puis vue_1_bande.png, vue_2_bande.png… (bandes horizontales pleine résolution, de haut en bas, qui se CHEVAUCHENT d'environ 120 px : une ligne coupée ou répétée à une jointure ne se transcrit qu'une fois). Transcris à partir des bandes.

Règles :
1. Une ligne de sortie par ligne imprimée, dans l'ordre de lecture. Folio (numéro de page), titre courant, signature (ex. « A 2 »), réclame (mot en bas à droite), manchettes/notes marginales : CHACUN sur sa propre ligne, à sa place dans l'ordre de lecture (haut → bas). Ornements, filets, vignettes : non transcrits.
2. Espaces UNIQUEMENT entre mots. La ponctuation (, . ; : ? ! / ) ]) est collée au mot précédent, même si l imprimé montre un blanc ; le mot SUIVANT la ponctuation en reste séparé par une espace (« wirt/ ſonder »). Pas d espace autour d un trait d union.
3. ſ (s long) distingué de s ; ß tel qu'imprimé ; ꝛ (U+A75B) pour le r rotunda.
4. Voyelle surmontée d'un petit e : voyelle + U+0364 (aͤ oͤ uͤ) ; deux points : ä ö ü. Regarde chaque signe suscrit de près.
5. Trait d'union Fraktur double oblique : ⸗ (U+2E17) ; trait simple (romain, ou trait droit) : -.
6. Ligatures consonantiques (ch, ck, ſt, ſſ, ſi, ll, tz, ff, fi, ct…) : lettres séparées. Æ æ œ Œ tels qu'imprimés.
7. Abréviations non développées, avec leur signe (ã ẽ ĩ õ ũ, n̄ ou ñ selon la forme du signe : barre droite ‾ = macron, ondulé ~ = tilde ; q́, ꝰ, etc.).
8. Majuscule Fraktur I/J : même famille de glyphe ; écris J si le glyphe descend sous la ligne de base, I sinon.
9. Orthographe, casse, accents, ponctuation : exactement comme imprimé. Aucune correction, modernisation ni complétion. Petites capitales → majuscules. Illisible : meilleur choix visuel.
10. Relis ta transcription contre les bandes, ligne par ligne et caractère par caractère, avant de rendre.

Sortie : le texte brut seul, sans markdown ni commentaire.

## Vues de détail (en plus des bandes)
En plus de vue_0 et des bandes, tu disposes de vues zoom_{k}_g.png et zoom_{k}_d.png : la bande k coupée en moitié gauche (g) et moitié droite (d), qui se recouvrent légèrement au milieu, agrandies 1,6×. Utilise les bandes pour la structure des lignes et l'ordre ; utilise les vues zoom pour trancher chaque détail fin : signes suscrits (deux points ä / petit e aͤ / rond ů), ſ contre f, ponctuation, chiffres, abréviations. Consulte systématiquement la vue zoom pour tout mot portant un signe suscrit.
