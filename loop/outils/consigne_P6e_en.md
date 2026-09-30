# Diplomatic transcription instructions (OCR-D level 2)

You are transcribing an early printed page (German Fraktur, Latin, French, Low German…), 1500-1830.

Views provided: vue_0_page.png (whole page, reduced, for the layout) then vue_1_bande.png, vue_2_bande.png… (full-resolution horizontal strips, top to bottom, which OVERLAP by about 120 px: a line cut or repeated at a join is transcribed only once). Transcribe from the strips.

Rules:
1. One output line per printed line, in reading order. Two distinct blocks of text placed on the same line but separated by a large blank (end of a paragraph then a date or signature aligned right; two columns; text then a reference or number aligned right): TWO output lines, left block then right block. Blanks between the syllables or letters of one word separate nothing. Folio (page number), running title, signature mark (e.g. "A 2"), catchword (word at bottom right), marginal notes: EACH on its own line, at its place in reading order (top → bottom). Ornaments, rules, vignettes: not transcribed.
2. Spaces ONLY between words. Punctuation (, . ; : ? ! / ) ]) is attached to the preceding word, even if the print shows a blank; the word FOLLOWING the punctuation stays separated from it by a space ("wirt/ ſonder"), including after the full stop of an abbreviation, even when tightly set in print: "l. non erit §. dato ff. de iureiur.", "cap. 3. v. 4." (never "l.non", "ff.de"). Exception: an initialism made of single letters tightly set in print ("v.c.", "d.i.") stays as printed. No space around a hyphen.
3. ſ (long s) distinguished from s; ß as printed; ꝛ (U+A75B) for r rotunda.
4. Vowel with a small e above: vowel + U+0364 (aͤ oͤ uͤ); two dots: ä ö ü. Look closely at every superscript sign.
5. Fraktur double oblique hyphen: ⸗ (U+2E17); single stroke (roman, or straight stroke): -.
6. Consonant ligatures (ch, ck, ſt, ſſ, ſi, ll, tz, ff, fi, ct…): separate letters. Æ æ œ Œ as printed.
7. Abbreviations not expanded, with their sign (ã ẽ ĩ õ ũ, n̄ or ñ according to the shape of the sign: straight bar ‾ = macron, wavy ~ = tilde; q́, ꝰ, etc.).
8. Fraktur capital I/J: same glyph family; write J if the glyph descends below the baseline, I otherwise.
9. Spelling, case, accents, punctuation: exactly as printed. No correction, modernisation or completion. Small capitals → capitals. Illegible: best visual choice.
10. Reread your transcription against the strips, line by line and character by character, before handing it in.

Output: the plain text only, without markdown or comment.

## Detail views (in addition to the strips)
In addition to vue_0 and the strips, you have views zoom_{k}_g.png and zoom_{k}_d.png: strip k cut into a left half (g) and a right half (d), which overlap slightly in the middle, enlarged 1.6×. Use the strips for the line structure and order; use the zoom views to decide every fine detail: superscript signs (two dots ä / small e aͤ / ring ů), ſ versus f, punctuation, digits, abbreviations. Always consult the zoom view for any word carrying a superscript sign.

## Script declaration (first line of your output)
Start your output with a line exactly of the form `#ECRITURE: fraktur`, `#ECRITURE: romain` or `#ECRITURE: mixte` according to the type family of the running text (Fraktur/Schwabacher = fraktur; Antiqua/italic = romain; both in comparable proportion = mixte). This line will be removed; all other lines are the transcription.
Quotation marks: reproduce their exact shape and position (« » „ “ ” ‚ ‘ ’); in German, the low mark „ is frequent at the start of a line.

## Role of each line (logical structure, same pass)
Prefix EACH transcription line with its role in square brackets, followed by a space, chosen from this list (OCR-D types):
[page-number] folio; [header] running title; [heading] title or subheading within the page; [paragraph] running text; [marginalia] marginal note; [footnote] footnote; [signature-mark] signature mark (e.g. "A 2"); [catch-word] catchword; [caption] caption; [other] other.
For running text, write [paragraph+] (with a +) on the FIRST line of each new paragraph (indent, or resumption after a title), and [paragraph] on the following lines of the same paragraph. Same rule for marginal notes and footnotes: [marginalia+] / [footnote+] at the start of each new marginal note or footnote.
Example:
#ECRITURE: fraktur
[header] Von der Peſtilentz.
[page-number] 20
[paragraph+] Die erſte Zeile eines Abſatzes
[paragraph] die zweite Zeile deſſelben.
[catch-word] Die

## Clarifications (P5)
- Sign over u in early German: decide by the WORD, not only by the shape of the sign. A superscript o (often reduced to a small ring) marks the medieval diphthong "uo": zů, gůt, thůn, můt, brůder, blůt, bůch, trůg, ſůn → write ů. A superscript e (in all its forms: small e, loop, two dots, stroke, hook) marks the umlaut ü: fuͤr, uͤber, Suͤnde, muͤſſen, fuͤhren, duͤnn, bluͤhen → write uͤ (or ü if they are clearly two separate dots, in roman type). If the modern word is spelled with ü, it is not ů.
- The ſz ligature (a ſ whose foot extends into a z tail, or a ſ followed by an attached z) is written ß. A lone ſ has no tail: compare with other ſ on the page before choosing.
- Regions: a new region ([paragraph+] etc.) starts only at a visible change of block: indented paragraph, vertical blank, title, change of type size or column. A list of items (proverbs, verses, dictionary entries) without indent or blank between them remains ONE single region.

## Special signs (P6)
- Fraction printed as a single block (stacked or reduced digits): Unicode fraction character (½ ⅓ ¼ ¾ ⅛), never "1/2".
- Currency signs printed as ONE special glyph (fused letters, loop, bar, a shape that is not a sequence of ordinary letters): write the ASCII token {florin} (florin/Gulden) or {groschen} (groschen), braces included, in place of the glyph (e.g. "3 {florin}. 15 Kaiſ. {groschen}."); they will be converted into OCR-D PUA codes (U+F2E8, U+F2E9). If they are printed as ordinary letters ("fl." as an ordinary ﬂ ligature, "Gr."), write those letters.
- Never transcribe an unknown sign with letters that resemble it ("fk", "gK"): choose the sign from the list above or, failing that, the character closest in function.
