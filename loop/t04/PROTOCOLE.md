# T04 — ů → uͤ par lexique (pré-enregistré 30/09 18h35)

Constat (types d'erreurs, 58 pages) : première classe = « uͤ » (VT) lu « ů » (20 signes, 5 pages). Planche de mots (herrleyc/41) : l'imprimeur emploie le même petit anneau pour l'inflexion (« Sůnde », « fůr », « důnner », « gefůndigt ») ; la VT transcrit par la fonction (uͤ), nos lecteurs par la forme, malgré la consigne P5 (« tranche par le MOT »). Une vérification visuelle aggraverait ces cas (non lancée). Règle OCR-D niveau 2 (L38) : « Umlaute entsprechend der Vorlage », sans cas de l'anneau.
Règle T04 (post-traitement, sans VLM) : dans chaque mot contenant « ů », si le mot avec « ü » est connu du lexique allemand hunspell de_DE (igerman98/frami, avec flexions) et le mot avec « u » ne l'est pas (ſ → s, ponctuation retirée), « ů » devient « u » + U+0364. Sinon inchangé.
Critère figé : texte glyphe (58 pages) total en baisse, aucune page en hausse ; O23-O25 rapporté.

## Résultat T04 — REJETÉE
4 mots changés, tous sur herbdulc/56 (Sůnde/, zukůnftige, Trůbſal/, ůber → uͤ) ; herbdulc 4 → 8 : pour ce livre, la VT garde « ů » sur ces mots d'inflexion, alors que sur herrleyc elle écrit « uͤ » sur des mots semblables. La convention ů/uͤ de la VT dépend du livre (ou de l'annotateur) : ni la forme vue (T04 visuel, non lancé) ni le mot (T04 lexique) ne la reproduit sur tout le corpus. Classe d'erreur à considérer comme bruit de convention de la référence (≈ 26 signes sur 240).
