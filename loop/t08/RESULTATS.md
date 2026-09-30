# T08 — signal gratuit pour cibler la relecture des blancs (T07c) — NÉGATIF (30/09 18h55)

Question : T07c (relecture aveugle des blancs, sûre mais 2 passes VLM/page) ne rapporte que si on sait où relire. Signal CPU candidat : nombre de mots de notre ligne lue ≠ nombre de mots de Calamari (calamari_bin) et/ou de Tesseract sur la même ligne (appariement par similarité de caractères ≥ 0,5). Mesuré avant toute passe VLM (outils/t08sig.py).

Vérité : ligne fausse = nombre de mots lu ≠ nombre de mots VT (lignes ≥ 2 mots, 60 pages, 1 694 lignes, 48 fausses — y compris celles exclues de CRITERE par C02b/C02c).

| signal | lignes signalées | fausses couvertes (rappel) | précision |
|---|---|---|---|
| Calamari ≠ | 480 (28 %) | 26/48 (54 %) | 5 % |
| Tesseract ≠ | 810 (48 %) | 35/48 (73 %) | 4 % |
| les deux ≠ | 335 (20 %) | 20/48 (42 %) | 6 % |

- Calamari soude souvent aux mêmes endroits que nous (« ihmviel », « VerboDri », « Krieges⸗und », « nimmt⸗ ») : erreurs corrélées, le signal manque justement les cas visés.
- Relire 20 % des lignes pour 42 % des fautes, avec un garde-fou T07c qui n'a corrigé qu'une page sur 11 : coût/bénéfice défavorable. Piste close ; T07c reste en réserve pour un mode qualité (toutes les lignes).
- Inventaire utile des 18 lignes CRITERE en échec pour nombre de mots (27 lignes en échec au total, 42/60) : soudures de lecture (« Thren.3. », « ihmviel », « Glaͤubigetragen », « VerboDEI », « Exerc.107.diſt.2. », « Krieges⸗und », « nimmt⸗ » ×2), coupures (« traher e », « vff kommen », « dē nachgeenden »), blancs discutables (« aeuo »/« a euo », « v. c. »), erreurs de ligne (hermhyst « zu Babylon » fusionnée, 852691769 césure de colonne, AyrmThes « De » absent, 688357687 titre courant). Les 9 autres : lignes sans boîte (oracle D).
