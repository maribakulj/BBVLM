# W04 — placement des mots par alignement CTC kraken (modèle CATMuS-Print fondue large)

Exploratoire (non pré-enregistré comme adoption) : branche CTC de compose.py, disponible depuis l'installation du modèle CATMuS-Print (accès internet illimité), lancée sur O18 (MODE=chaine2, crit18) ; tout le reste de la chaîne par défaut.

| page | défaut (etat_0930) | CTC CATMuS |
|---|---|---|
| brieetli/738 | ≤0,5c 95,78 pire 1,32 IoU 0,971 ✓ | 93,37 / 1,32 / 0,926 ✗ |
| brochrnx/730 | 99,06 / 0,67 / 0,978 ✓ | 99,06 / 0,67 / 0,977 ✓ |
| geomeikud/82 | 100,0 / 0,16 / 0,918 ✗ | 98,68 / 3,18 / 0,911 ✗ |
| herrleyc/749 | 98,55 / 0,76 / 0,951 ✓ | 97,83 / 0,87 / 0,938 ✓ |

CRITERE 2/4 contre 3/4 ; aucune page ne s'améliore, trois se dégradent. **Rejeté** sans extension aux autres lots (une dégradation sur toutes les pages suffit). Cause probable : les frontières de caractères CTC d'un modèle générique sont décalées de quelques pixels (pics CTC en avance, cf. littérature sur l'alignement CTC), alors que le placeur actuel (W02 + ancrage Tesseract) colle aux blancs d'encre.
