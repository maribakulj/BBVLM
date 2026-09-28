# A74 — transfert figé du masque de lignes Eynollah

## Question

Le rappel dense observé en A72 sur deux pages consommées transfère-t-il à des
pages diverses qui n'ont servi ni à A72 ni à A73 ? Cette étape mesure seulement
si le masque de lignes est une preuve structurale utile. Elle ne fabrique pas
encore de boîtes ALTO et ne peut valider ni l'OCR ni l'ordre de lecture.

## Gel avant ouverture

- Source : split officiel `Training` de Chronicling Germany ; `Validation` a été
  consommé par A65 et les 100 pages `Test` restent fermées.
- Exclusions : les dix pages A69, donc aussi les deux pages A72/A73.
- Quatre strates temporelles : 1600–1749, 1750–1849, 1850–1900, 1901–1945.
- Dans chaque strate, choisir la page au plus petit SHA-256 de
  `A74-v1:<identifiant>`. Le choix n'utilise ni pixels ni géométrie XML.
- Le split et ce protocole sont écrits avant téléchargement des images et avant
  toute lecture des annotations de ces pages pour le score A74.

## Méthode figée

Exécuter uniquement le SavedModel de lignes Eynollah déjà haché en A72, avec
exactement la même largeur 2000, tuiles 672, marge 67 et agrégation de tuiles.
Écrire et hacher les quatre masques avant d'ouvrir les XML. Ne pas exécuter le
pipeline Eynollah complet, l'OCR, un VLM ou DocLayout-YOLO.

Pour chaque polygone `TextLine`, mesurer la fraction couverte par le masque. Au
niveau page, mesurer aussi (a) la fraction du masque contenue dans l'union des
polygones ligne et (b) la fraction de cette union couverte par le masque.

## Seuils locaux préenregistrés

Le diagnostic transfère seulement si :

1. au moins 99 % des lignes ont au moins 1 % de couverture ;
2. chaque page a au moins 75 % de pixels du masque dans l'union des lignes ;
3. l'union des lignes est couverte à au moins 50 % en agrégé ;
4. aucun fichier du split `Test` n'est ouvert.

Même en cas de réussite, aucun gate global n'est promu : les polygones PAGE ne
sont pas une vérité parfaite, un masque n'est pas une boîte ALTO et le split
Training a déjà subi l'audit structurel global A58.

