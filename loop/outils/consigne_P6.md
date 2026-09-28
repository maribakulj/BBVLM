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

## Déclaration d'écriture (première ligne de ta sortie)
Commence ta sortie par une ligne exactement de la forme `#ECRITURE: fraktur`, `#ECRITURE: romain` ou `#ECRITURE: mixte` selon la famille de caractères du texte courant (Fraktur/Schwabacher = fraktur ; Antiqua/italique = romain ; les deux en proportion comparable = mixte). Cette ligne sera retirée ; toutes les autres lignes sont la transcription.
Guillemets : reproduis leur forme et leur position exactes (« » „ “ ” ‚ ‘ ’) ; en allemand, le guillemet bas „ est fréquent en début de ligne.

## Rôle de chaque ligne (structure logique, même passe)
Préfixe CHAQUE ligne de transcription par son rôle entre crochets, suivi d'une espace, choisi dans cette liste (types OCR-D) :
[page-number] folio ; [header] titre courant ; [heading] titre ou intertitre dans la page ; [paragraph] texte courant ; [marginalia] manchette/note marginale ; [footnote] note de bas de page ; [signature-mark] signature (ex. « A 2 ») ; [catch-word] réclame ; [caption] légende ; [other] autre.
Pour le texte courant, écris [paragraph+] (avec un +) sur la PREMIÈRE ligne de chaque nouveau paragraphe (alinéa, retrait, ou reprise après un titre), et [paragraph] sur les lignes suivantes du même paragraphe. Même règle pour les manchettes et notes : [marginalia+] / [footnote+] au début de chaque nouvelle manchette ou note.
Exemple :
#ECRITURE: fraktur
[header] Von der Peſtilentz.
[page-number] 20
[paragraph+] Die erſte Zeile eines Abſatzes
[paragraph] die zweite Zeile deſſelben.
[catch-word] Die

## Précisions (P5)
- Signe sur u en allemand ancien : tranche par le MOT, pas seulement par la forme du signe. Un o suscrit (souvent réduit à un petit anneau) note la diphtongue médiévale « uo » : zů, gůt, thůn, můt, brůder, blůt, bůch, trůg, ſůn → écris ů. Un e suscrit (sous toutes ses formes : petit e, boucle, deux points, trait, crochet) note l'inflexion ü : fuͤr, uͤber, Suͤnde, muͤſſen, fuͤhren, duͤnn, bluͤhen → écris uͤ (ou ü si ce sont nettement deux points séparés, en caractères romains). Si le mot moderne s'écrit avec ü, ce n'est pas ů.
- La ligature ſz (un ſ dont le bas se prolonge en queue de z, ou un ſ suivi d'un z accolé) s'écrit ß. Un ſ seul n'a pas de queue : compare avec d'autres ſ de la page avant de choisir.
- Régions : une nouvelle région ([paragraph+] etc.) commence seulement à un changement visible de bloc : alinéa en retrait, blanc vertical, titre, changement de corps ou de colonne. Une liste d'items (proverbes, vers, articles de dictionnaire) sans retrait ni blanc entre eux reste UNE seule région.

## Signes spéciaux (P6)
- Fraction imprimée d'un seul bloc (chiffres empilés ou réduits) : caractère Unicode de fraction (½ ⅓ ¼ ¾ ⅛), jamais « 1/2 ».
- Signes monétaires imprimés comme UN glyphe spécial (lettres fondues, boucle, barre, forme qui n'est pas une suite de lettres ordinaires), écris le jeton ASCII {florin} (florin/Gulden) ou {groschen} (groschen), accolades comprises, à la place du glyphe (ex. « 3 {florin}. 15 Kaiſ. {groschen}. ») ; ils seront convertis en codes PUA OCR-D (U+F2E8, U+F2E9). S'ils sont imprimés en lettres ordinaires (« fl. » en ligature ﬂ ordinaire, « Gr. »), écris ces lettres.
- Ne transcris jamais un signe inconnu par des lettres qui lui ressemblent (« fk », « gK ») : choisis le signe de la liste ci-dessus ou, à défaut, le caractère le plus proche par sa fonction.
