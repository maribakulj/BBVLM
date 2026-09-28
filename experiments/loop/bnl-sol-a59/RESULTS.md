# A59 — lecture Sol native : variante rejetée

Six blocs A54 consommés, quatre résidus lexicaux élevés et deux témoins exacts. Une session gpt-6-sol, six images inspectées en détail original, aucune transcription ni référence montrée.

| Mesure | Luna guard A54 | Sol aveugle |
|---|---:|---:|
| CER lexical (sans espaces/ponctuation) | 24/4990 = 0,481 % | 57/4990 = 1,142 % |
| CER recherche | 54/6291 = 0,858 % | 74/6291 = 1,176 % |
| Témoins exacts lexical/recherche | 2/2 | 2/2 |

Le bloc 0455 (luxembourgeois ancien, italique, 893×3059 px) concentre la dégradation : 8→45 éditions lexicales. 0009 gagne5→3 ; 0345 gagne8→5 ; 0231 dégrade3→4. Ce test ne compare pas seulement les modèles : Luna avait PERO, Sol lit les pixels seuls. Il ne permet donc pas de conclure que Sol est intrinsèquement moins bon. Il rejette la substitution aveugle testée.

Audit visuel parent sur 0345 et 0455, après score : sur0345, l’image soutient clairement « la belle », « vous », « écoutez » et « votre », contre « ja belle », « vons », « éeoutez » et « vore » dans la référence. Quatre désaccords paraissent donc provenir de la référence. La présence de l’accent de « brûlant » reste à adjuger. Original XML inchangé ; ces observations ne sont pas une nouvelle GT indépendante. Sur0455, accents peu lisibles dans un bloc très haut : tester le même contenu en bandes natives courtes avant une décision sur les glyphes.

Coût : six images, zéro nouveau détecteur/OCR, tokens non exposés. IDs et empreintes contrôlés ; aucun objectif global validé. A60 prévoira une ablation de présentation par trois bandes de même source, sans modifier pixels, modèle ni consigne de transcription. Diagnostic sur bloc consommé.
