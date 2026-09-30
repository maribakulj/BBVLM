# Anweisung zur diplomatischen Transkription (OCR-D Level 2)

Du transkribierst eine alte gedruckte Seite (deutsche Fraktur, Latein, Französisch, Niederdeutsch…), 1500-1830.

Bereitgestellte Ansichten: vue_0_page.png (ganze Seite, verkleinert, für das Layout), dann vue_1_bande.png, vue_2_bande.png… (waagerechte Streifen in voller Auflösung, von oben nach unten, die sich um etwa 120 px ÜBERLAPPEN: eine an einer Nahtstelle abgeschnittene oder wiederholte Zeile wird nur einmal transkribiert). Transkribiere anhand der Streifen.

Regeln:
1. Eine Ausgabezeile pro gedruckter Zeile, in Lesereihenfolge. Zwei getrennte Textblöcke auf derselben Zeile, die durch einen großen Leerraum getrennt sind (Absatzende, dann rechtsbündiges Datum oder Unterschrift; zwei Spalten; Text, dann rechtsbündiger Verweis oder Nummer): ZWEI Ausgabezeilen, linker Block, dann rechter Block. Leerräume zwischen den Silben oder Buchstaben eines Wortes trennen nichts. Blattzahl (Seitenzahl), Kolumnentitel, Bogensignatur (z. B. „A 2“), Kustode (Wort unten rechts), Marginalien/Randnoten: JEDES auf einer eigenen Zeile, an seiner Stelle in der Lesereihenfolge (oben → unten). Ornamente, Linien, Vignetten: werden nicht transkribiert.
2. Leerzeichen NUR zwischen Wörtern. Satzzeichen (, . ; : ? ! / ) ]) werden an das vorhergehende Wort angehängt, auch wenn der Druck einen Leerraum zeigt; das Wort NACH dem Satzzeichen bleibt durch ein Leerzeichen getrennt („wirt/ ſonder“), auch nach dem Punkt einer Abkürzung, selbst wenn eng gesetzt: „l. non erit §. dato ff. de iureiur.“, „cap. 3. v. 4.“ (nie „l.non“, „ff.de“). Ausnahme: ein im Druck eng gesetztes Kürzel aus Einzelbuchstaben („v.c.“, „d.i.“) bleibt wie gedruckt. Kein Leerzeichen um einen Bindestrich.
3. ſ (langes s) von s unterschieden; ß wie gedruckt; ꝛ (U+A75B) für das r rotunda.
4. Vokal mit kleinem e darüber: Vokal + U+0364 (aͤ oͤ uͤ); zwei Punkte: ä ö ü. Sieh dir jedes übergesetzte Zeichen genau an.
5. Doppelter schräger Fraktur-Bindestrich: ⸗ (U+2E17); einfacher Strich (Antiqua oder gerader Strich): -.
6. Konsonantenligaturen (ch, ck, ſt, ſſ, ſi, ll, tz, ff, fi, ct…): getrennte Buchstaben. Æ æ œ Œ wie gedruckt.
7. Abkürzungen nicht aufgelöst, mit ihrem Zeichen (ã ẽ ĩ õ ũ, n̄ oder ñ je nach Form des Zeichens: gerader Strich ‾ = Makron, gewellt ~ = Tilde; q́, ꝰ usw.).
8. Fraktur-Großbuchstabe I/J: dieselbe Glyphenfamilie; schreibe J, wenn die Glyphe unter die Grundlinie reicht, sonst I.
9. Rechtschreibung, Groß- und Kleinschreibung, Akzente, Zeichensetzung: genau wie gedruckt. Keine Korrektur, Modernisierung oder Ergänzung. Kapitälchen → Großbuchstaben. Unleserlich: beste visuelle Wahl.
10. Lies deine Transkription vor der Abgabe Zeile für Zeile und Zeichen für Zeichen gegen die Streifen gegen.

Ausgabe: nur der reine Text, ohne Markdown und ohne Kommentar.

## Detailansichten (zusätzlich zu den Streifen)
Zusätzlich zu vue_0 und den Streifen hast du die Ansichten zoom_{k}_g.png und zoom_{k}_d.png: Streifen k, geteilt in linke Hälfte (g) und rechte Hälfte (d), die sich in der Mitte leicht überlappen, 1,6-fach vergrößert. Nutze die Streifen für die Zeilenstruktur und die Reihenfolge; nutze die Zoomansichten, um jedes feine Detail zu entscheiden: übergesetzte Zeichen (zwei Punkte ä / kleines e aͤ / Kringel ů), ſ gegen f, Satzzeichen, Ziffern, Abkürzungen. Ziehe für jedes Wort mit einem übergesetzten Zeichen systematisch die Zoomansicht heran.

## Schriftangabe (erste Zeile deiner Ausgabe)
Beginne deine Ausgabe mit einer Zeile genau der Form `#ECRITURE: fraktur`, `#ECRITURE: romain` oder `#ECRITURE: mixte`, je nach Schriftfamilie des Fließtextes (Fraktur/Schwabacher = fraktur; Antiqua/Kursive = romain; beide in vergleichbarem Anteil = mixte). Diese Zeile wird entfernt; alle anderen Zeilen sind die Transkription.
Anführungszeichen: gib ihre genaue Form und Position wieder (« » „ “ ” ‚ ‘ ’); im Deutschen steht das untere „ häufig am Zeilenanfang.

## Rolle jeder Zeile (logische Struktur, im selben Durchgang)
Setze vor JEDE Transkriptionszeile ihre Rolle in eckigen Klammern, gefolgt von einem Leerzeichen, gewählt aus dieser Liste (OCR-D-Typen):
[page-number] Blattzahl; [header] Kolumnentitel; [heading] Titel oder Zwischentitel auf der Seite; [paragraph] Fließtext; [marginalia] Marginalie/Randnote; [footnote] Fußnote; [signature-mark] Bogensignatur (z. B. „A 2“); [catch-word] Kustode; [caption] Bildunterschrift; [other] Sonstiges.
Schreibe beim Fließtext [paragraph+] (mit einem +) auf die ERSTE Zeile jedes neuen Absatzes (Einzug oder Wiederbeginn nach einem Titel) und [paragraph] auf die folgenden Zeilen desselben Absatzes. Dieselbe Regel für Marginalien und Fußnoten: [marginalia+] / [footnote+] am Anfang jeder neuen Marginalie oder Fußnote.
Beispiel:
#ECRITURE: fraktur
[header] Von der Peſtilentz.
[page-number] 20
[paragraph+] Die erſte Zeile eines Abſatzes
[paragraph] die zweite Zeile deſſelben.
[catch-word] Die

## Präzisierungen (P5)
- Zeichen über u im älteren Deutsch: entscheide nach dem WORT, nicht nur nach der Form des Zeichens. Ein übergesetztes o (oft zu einem kleinen Kringel verkleinert) bezeichnet den mittelalterlichen Diphthong „uo“: zů, gůt, thůn, můt, brůder, blůt, bůch, trůg, ſůn → schreibe ů. Ein übergesetztes e (in allen Formen: kleines e, Schleife, zwei Punkte, Strich, Häkchen) bezeichnet den Umlaut ü: fuͤr, uͤber, Suͤnde, muͤſſen, fuͤhren, duͤnn, bluͤhen → schreibe uͤ (oder ü, wenn es in Antiqua deutlich zwei getrennte Punkte sind). Wird das moderne Wort mit ü geschrieben, ist es kein ů.
- Die Ligatur ſz (ein ſ, dessen Fuß in einen z-Schwanz übergeht, oder ein ſ mit angesetztem z) wird ß geschrieben. Ein einzelnes ſ hat keinen Schwanz: vergleiche vor der Entscheidung mit anderen ſ der Seite.
- Regionen: eine neue Region ([paragraph+] usw.) beginnt nur bei einem sichtbaren Blockwechsel: eingerückter Absatz, senkrechter Leerraum, Titel, Wechsel des Schriftgrads oder der Spalte. Eine Liste von Einträgen (Sprichwörter, Verse, Wörterbuchartikel) ohne Einzug oder Leerraum dazwischen bleibt EINE einzige Region.

## Sonderzeichen (P6)
- Als ein einziger Block gedruckter Bruch (übereinander gesetzte oder verkleinerte Ziffern): Unicode-Bruchzeichen (½ ⅓ ¼ ¾ ⅛), nie „1/2“.
- Als EINE Sonderglyphe gedruckte Münzzeichen (verschmolzene Buchstaben, Schleife, Strich, eine Form, die keine Folge gewöhnlicher Buchstaben ist): schreibe anstelle der Glyphe das ASCII-Token {florin} (Florin/Gulden) oder {groschen} (Groschen), einschließlich der geschweiften Klammern (z. B. „3 {florin}. 15 Kaiſ. {groschen}.“); sie werden in OCR-D-PUA-Codes umgewandelt (U+F2E8, U+F2E9). Sind sie mit gewöhnlichen Buchstaben gedruckt („fl.“ als gewöhnliche ﬂ-Ligatur, „Gr.“), schreibe diese Buchstaben.
- Transkribiere ein unbekanntes Zeichen nie mit Buchstaben, die ihm ähneln („fk“, „gK“): wähle das Zeichen aus der obigen Liste oder, falls keines passt, das der Funktion nach nächstliegende Zeichen.
