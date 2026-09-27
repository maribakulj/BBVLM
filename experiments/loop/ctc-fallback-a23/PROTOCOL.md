# A23 — fallback CTC ciblé, protocole figé

La réserve A22 est déjà consommée. Cette expérience est donc un diagnostic
postérieur sur des entrées fixes, jamais une validation indépendante.

## Hypothèse

Le fast-path A19 conserve ses propositions sur les lignes qu'il accepte. Pour
les 14/16 lignes refusées, une seule passe de reconnaissance PERO met en cache
les logits CTC. La transcription Sol A22 est ensuite alignée sur ces logits sans
nouvelle passe réseau. Les mots utilisent soit les boîtes ALTO natives de cet
alignement, soit les mêmes séparateurs CTC avec une étendue resserrée sur
l'encre. Le texte final reste exactement le texte Sol; une transcription proxy
compatible avec le codec peut uniquement guider la géométrie.

## Configuration figée avant mesure

- PERO OCR 0.7.0, modèle public `pero_eu_cz_print_newspapers_2022-09-26`;
- SHA-256 de l'archive: `cb38dd0792c7145b8ba4dd64df255980e4633f4ca1d406f7f230b9c174c0c70d`;
- CPU, quatre threads, parseur de layout désactivé;
- les 16 polygones de lignes A22 servent d'oracle conditionnel;
- baseline synthétique horizontale à 80 % de la hauteur du rectangle de ligne;
- proxy: NFC, puis décomposition sans diacritiques seulement pour les caractères
  absents du codec, puis U+FFFD en dernier recours; aucun espace n'est ajouté ou
  supprimé;
- `ink_span`: séparateurs aux milieux des boîtes CTC adjacentes, étendue à toutes
  les colonnes d'encre du masque de ligne dans chaque intervalle;
- hybride: boîte A19 si la ligne avait été acceptée, sinon `ink_span`;
- mesures: appariement hongrois géométrique, précision/rappel IoU >= 0,5 et 0,8,
  IoU moyen des paires, couverture, échecs codec, temps chargement/reconnaissance/
  alignement. Les omissions restent dans le dénominateur du rappel.

Les XML/images/réponses A22 sont protégés par hash et ne sont pas modifiés.

