# Objectif — produire de la vérité terrain ALTO, pas concurrencer un OCR

## Le constat qui fonde le projet

| | production de masse | **production de vérité terrain** |
|---|---|---|
| ce qui compte | débit, coût par page | **exactitude** |
| CTC assorti (kraken `german_print`) | ✅ 3 s/page, **1,25 %** de CER | ❌ 1,25 % est ce qu'une VT doit corriger |
| VLM de frontière | ❌ lent, coûteux | ✅ **0,00 %** mesuré sur 12 lignes de Fraktur |
| géométrie au mot | fournie par le CTC | **à reconstruire** — un VLM se trompe de 367 px |

Pour de la production de masse, un moteur classique assorti gagne sans discussion.
**Pour produire une VT, 1,25 % ne suffit pas**, et le coût par page n'a aucune
importance quand on annote quelques dizaines de pages une seule fois.

## Le goulot que ça débloque

Mesuré en cherchant un corpus d'épreuve : **la vérité terrain au mot est rare**.
GT4HistOCR, AustrianNewspapers, la plupart des sorties Transkribus s'arrêtent à
la ligne — c'est ce dont un CTC a besoin pour s'entraîner, et les boîtes de mots
ne servent qu'à l'aval.

Ce système produit précisément ce qui manque.

## La chaîne

```
image de page
   ↓  kraken / eynollah        lignes, polygones, lignes de base
   ↓  VLM de frontière         texte au caractère près
   ↓  moteur géométrique       boîtes de mots à 0,47 caractère près
   ↓  contrôles                refuser plutôt qu'inventer
ALTO 4.4 + overlay de relecture humaine
```

## Ce qui distingue une sortie de VT d'une sortie d'OCR

1. **Elle refuse.** Une ligne douteuse est signalée, jamais comblée. Le compte de
   lignes et le coût d'alignement mot/encre le permettent sans vérité terrain.
2. **Elle est relue.** Un overlay accompagne chaque page ; sans relecture humaine,
   ce n'est pas une VT mais une sortie d'OCR de plus.
3. **Elle déclare sa provenance.** Quel modèle a lu, quel moteur a placé, quelles
   lignes ont été reprises ou écartées.

## Ce qui reste à démontrer

- la dérive du VLM à l'échelle de la page (churro dérivait sur 2 pages sur 5 ;
  un modèle de frontière dérive moins, « moins » n'est pas « jamais ») ;
- la géométrie sur une écriture sans VT au mot — le banc n'en a pas ;
- le taux de reprise humaine réellement nécessaire.

Le critère de qualité des boîtes reste celui de `CRITERE.md`, gelé et inchangé :
il devient plus exigeant, pas moins, puisqu'une VT ne tolère pas l'à-peu-près.
