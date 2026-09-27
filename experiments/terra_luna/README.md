# Pilote Terra / Luna — 27 septembre 2026

Deux sous-agents ont réellement inspecté les mêmes six images : la page originale,
la page avec les identifiants de régions et quatre planches contenant 25 lignes.
Modèles demandés : `gpt-5.6-terra` et `gpt-6-luna`, effort `high`, contexte initial
vierge, même consigne. Aucun texte OCR ou de référence fourni lors de la première
lecture. Les sorties originales sont conservées sans retouche.

## Corpus et attribution

Page `ONB_aze_18950706_2`, *Arbeiter-Zeitung*, 6 juillet 1895, page 2.
NewsEye / READ, Bibliothèque nationale d'Autriche ; révision Universitätsbibliothek
Mannheim, AustrianNewspapers 2.0, OCR-D. Jeu original : Mühlberger & Hackl (2019),
https://doi.org/10.5281/zenodo.3387369, licence CC BY 4.0.

Source : https://github.com/UB-Mannheim/AustrianNewspapers
Révision relevée : `92cd4e51f8f0bd8249ab6bdd999d7c4ce392463c`.
Fichiers dans `data/TrainingSet_ONB_Newseye_GT_M1+/GT-PAGE/`.
Les images du pilote sont des crops et une copie annotée de cette source.

Sélection mécanique : les trois premières lignes de chaque région, ou moins
si la région en contient moins. **25 lignes sur 354, 916 caractères**, avec
géométrie des lignes/régions fournie par la référence. Pas de sélection selon
les erreurs et pas de mesure des boîtes de mots dans cette expérience.

## Résultats mesurés

| Modèle | CER strict, passe initiale | CER NFC + ſ→s | CER strict après reprise | CER NFC + ſ→s après reprise |
|---|---:|---:|---:|---:|
| Terra | 2,51 % (23 edits) | 0,55 % (5 edits) | 2,29 % (21 edits) | 0,33 % (3 edits) |
| Luna | 1,86 % (17 edits) | 0,66 % (6 edits) | 1,42 % (13 edits) | 0,55 % (5 edits) |

Les deux modèles rendent 25/25 identifiants. La référence distingue `ſ` et `s`,
ainsi que `⸗` et `-`. La colonne normalisée ne remplace que `ſ→s` et applique NFC ;
elle ne supprime ni ponctuation ni erreurs lexicales. Ce sont des distances à une
référence publiée, pas une certification indépendante de son infaillibilité.

Une seule reprise a été demandée à chaque modèle, sur **quatre lignes**, choisies
par le désaccord des réponses après NFC + ſ→s. Les deux candidats étaient fournis,
sans référence. Les conventions n'ont pas été corrigées après coup dans les sorties.
Cette expérience ne mesure pas le coût d'un seul modèle : le routage par désaccord
nécessite ici deux lectures initiales.

Exemples : Terra modernisait `Oe` en `Ö` et le corrige à la reprise. Luna corrige
`bar` en `dar`, mais conserve `wie` au lieu de `nie` et un caractère supplémentaire
dans un patronyme. Les deux déclarent les quatre lignes sans incertitude après
reprise, malgré les erreurs restantes. Les trois `⸗` transformés en `-` sont des
erreurs communes que le désaccord ne détecte pas.

## Structure et métadonnées

- Les deux identifient les cinq en-têtes et les rôles titre/corps.
- Terra rattache 5 des 8 régions de contenu à ses groupes d'articles ; Luna 8/8.
  Cela mesure la couverture d'association, **pas la justesse des articles**.
- Terra fournit 6 champs de métadonnées ; Luna 8, avec les dates des articles en
  plus. Les noms des champs varient (`page`/`page_number`, etc.) : le vocabulaire
  doit être fixé avant un benchmark d'extraction de champs.
- Pas de score d'exactitude des articles : absence de référence arbitrée à ce niveau.
- Les identifiants séquentiels des régions reflètent l'ordre source. C'est une
  faiblesse du pilote : les résultats d'ordre de lecture ne constituent pas un
  benchmark aveugle. Une prochaine expérience devra randomiser les identifiants
  et l'ordre de présentation, sans modifier les coordonnées.

Les paquets `.package/` contiennent graphe, ALTO 4.4, METS 1.12.1 et file de
relecture. Tous les XML sont validés par les XSD complets. Les ALTO de ce pilote
sont **au niveau ligne, sans boîtes de mots inventées** : chaque ligne non alignée
contient un `String` explicitement marqué `UNALIGNED`, sans géométrie de mot.
La géométrie des lignes et régions est conservée. Ces paquets ne sont pas des VT
finales. `certified_ground_truth` reste faux.

## Reproduction

```bash
PYTHONPATH=src python scripts/prepare_vlm_pilot.py
PYTHONPATH=src python scripts/evaluate_vlm_pilot.py
```

La seconde commande rejoue les réponses enregistrées et valide les exports ;
elle ne rappelle pas les modèles. Les sous-agents ChatGPT ne sont pas une API
invocable depuis ce script. Temps GPU, tokens, prix et paramètres de décodage
n'étaient pas exposés : aucun chiffre de coût ni de débit n'est extrapolé.

Les références sont dans `reference/`, séparées des images/manifestes fournis aux
sous-agents. Cette séparation repose sur leurs consignes, pas sur une isolation
filesystem forte. Ce pilote ne démontre aucune généralisation à d'autres titres,
langues, mises en page ou documents hors données publiques.
