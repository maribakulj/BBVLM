# O16 — résultats (4 pages d'œuvres jamais vues par cette boucle)

Texte, sortie finale (mode qualité) contre référence adjugée (A2, deux arbitres) :

| page | car. | glyphe | diplo | norm | lecture A seule (glyphe) | réf. corrigée |
|---|---|---|---|---|---|---|
| chiamerk_766680207/97 | 1158 | **0** | 0 | 0 | 0 | 2 car. |
| briedefra_788606417/133 | 1797 | 1 | 1 | 1 | 1 | 0 |
| erasexom_816221448/29 (latin) | 1379 | 4 | 31 | — | 4 | 21 car. (1 indécidée) |
| brieetli_73862926X/30 | 1107 | 8 | 10 | 4 | 11 | 9 car. |

N01 sur pages neuves : aucune page ne monte ; erasexom 31 → 4 (ligature PUA
« ta », trait nasal tilde/macron). Mode économe = mode qualité sur 3 pages sur 4.

ALTO (texte+IoU80) : défaut 0,919 / 0,912 / 0,951 / 0,778 (somme 3,559) ;
sans G05 3,459 (briedefra 0,828, brieetli 0,902) ; sans H01, sans S08 : identique
(pas de page penchée ni de ligne fusionnée). Aucun recul : G05 validé (seuil fixé avant O16).

CRITERE : ✓ chiamerk, brieetli ; ✗ briedefra (≤0,5c 94,7 %, pire 4,0c),
erasexom (9 lignes en échec, nombre de mots). Toutes lignes trouvées (sauf 1 sur erasexom).
**chiamerk : quatrième page parfaite de bout en bout (texte 0 + CRITERE ✓), première sur œuvre neuve depuis O13.**

Recherche (ALTO, rappel / précision) : briedefra 0,993 / 0,990 ; brieetli 0,963 / 0,986 ;
chiamerk 0,985 / 1,000 ; erasexom 0,923 / 0,956.
OLR (lecture A) : rôles 0,95-1,0 ; F1 régions 0,72-1,0 ; ordre 0,83-1,0.

Restes texte (glyphe) : brieetli uͤ/ü (3, les arbitres lisent deux points ;
I01 sans décision nette), u/v ; briedefra J/I ; erasexom ß/ſſ, coquille VT
« trihuat » gardée (contestée), blanc. Échecs CRITERE d'erasexom (9 lignes) :
la VT colle ou coupe des mots (« benignus& », « Vbiſpũm », « ſacer doti ») ;
les arbitres ont corrigé ces blancs dans la référence adjugée, mais les boîtes
de mots de la VT suivent son découpage : nombre de mots différent, pas une
faute de notre sortie.
