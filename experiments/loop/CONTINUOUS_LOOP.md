# Boucle continue dans une session active

Le réveil programmé sert de reprise après interruption, pas de temporisateur entre expériences. Tant que l'agent est actif et qu'une action utile est possible, enchaîner immédiatement. Ne jamais attendre le prochain réveil pour poursuivre. Les limites du runtime peuvent néanmoins interrompre une session : aucun script ne garantit une présence permanente de Codex.

## Deux responsabilités explicites

- `scripts/experiment_queue.py` exécute les commandes locales déclarées dans `queue.json`, respecte les dépendances, écrit `queue-state.json`, et retourne les actions externes prêtes. Il ne sait ni consulter GitHub via le connecteur ni invoquer un sous-agent VLM.
- L'agent Codex actif consulte Claude, lit les articles, fige les hypothèses, lance de vrais lecteurs aveugles, vérifie les résultats, commit/push puis sauvegarde le checkpoint. Il ajoute les tâches suivantes à la file au lieu de conclure après un seul tour.

## Ordre de travail

1. Relire l'état, les processus/agents connus et la branche Claude `claude/astra-branch-analysis-wf4gj4`. Enregistrer le SHA et les nouveautés réellement lues avant chaque nouvelle hypothèse. Examiner également les nouveaux protocoles et scripts ; ne pas se limiter au journal si la branche a changé.
2. Choisir le défaut mesuré prioritaire. Consulter les sources primaires et le code pertinent. Résumer chaque article dans `PAPER_SUMMARIES.md` avec date, méthode, données, limites, pertinence BBVLM, et niveau de lecture (résumé/texte complet). Une optimisation de l'orchestrateur n'est pas un nouveau résultat scientifique OCR.
3. Déclarer les tâches et dépendances dans `queue.json`. Commandes en tableaux `argv`, aucune chaîne shell. Déclarer tous les scripts, configurations, modèles et fichiers d'entrée déterminants : seuls les inputs déclarés sont hachés. Une empreinte ne prouve pas l'absence de dépendance cachée.
4. Réserver le lecteur externe prêt AVANT de lancer une longue vague CPU. Lancer Luna (ou Sol sur motif explicite), puis exécuter les tâches CPU/fichiers indépendantes. Pendant ce calcul : lire les articles, inspecter le code ou préparer une autre piste, sans toucher aux inputs actifs. Ne pas attendre un agent si une action indépendante existe.
5. Réceptionner l'inférence réelle, valider IDs/images/schéma, déposer l'artefact puis acquitter la réservation. Les tâches de score deviennent alors prêtes. Une réponse produite n'est pas une vérité terrain ; la validation scientifique demeure séparée.
6. Après chaque expérience : documenter résultat positif/négatif, coût, limites et provenance ; vérifier les invariants ; commit et push sans force sur `codex/autonomous-research-a34` ; régénérer et remplacer le checkpoint persistant ; puis préparer et lancer immédiatement la suivante. La publication est une barrière avant la prochaine hypothèse, pas une action factice du lanceur.
7. Si une piste est bloquée (adjudication humaine, source absente, calcul en cours), avancer une autre piste utile : géométrie prédite, OLR, métadonnées sourcées ou retrieval à jugements indépendants. Ne jamais déclarer un gate vrai pour pouvoir arrêter.

## Commandes

```sh
python scripts/autonomous_loop.py --execute
# L'ancien pipeline délègue ensuite à la file, après libération du verrou commun.
python scripts/experiment_queue.py --execute --budget-seconds 2700
python scripts/experiment_queue.py
python scripts/experiment_queue.py --claim ID --actor IDENTIFIANT_REEL
python scripts/experiment_queue.py --complete ID --token JETON_RETOURNE
```

Les ressources par défaut sont : un calcul CPU (4 threads), deux tâches fichiers/réseau, un lecteur VLM, une action d'orchestration. Seules les commandes sont lancées par le script. Une réservation externe consomme sa ressource entre deux invocations ; l'agent actif peut donc lire pendant qu'une vague CPU tourne. Un processus conserve le verrou commun pendant sa vague : les mutations de file et acquittements attendent sa fin, les lectures externes et la recherche continuent.

Aucune pause de deux minutes n'est ajoutée. Le dispatcher scrute ses vrais processus enfants toutes les 50 ms ; il rend immédiatement la main quand seules des actions externes sont prêtes. Le budget de 2700 secondes borne une invocation CPU et n'est pas une attente ni une promesse de durée de session. Le réexécuter immédiatement s'il reste des commandes utiles prêtes et que le runtime le permet.

## Reprise prudente

Succès technique = code de retour 0 + tous les artefacts attendus présents, JSON décodable le cas échéant, inputs inchangés et hashes enregistrés. Cela ne valide pas leur vérité scientifique. Un simple ancien fichier ne vaut pas un reçu d'exécution.

Un changement d'input/output/dépendance rend la tâche `stale` sans l'écraser. Une commande restée `running` après perte du coordinateur devient `interrupted` et réserve encore sa ressource : inspecter le PID/groupe de processus enregistré et les artefacts avant de résoudre manuellement l'incident et créer une tentative avec nouvel ID et nouveaux outputs. Une réservation VLM ancienne ou périmée n'est jamais automatiquement relancée. Vérifier l'agent réel, conserver sa trace, puis libérer explicitement l'état seulement après résolution ; ne pas fabriquer une réponse pour débloquer la file. Conserver les jobs actifs dans le manifeste.

Ne pas envelopper un script qui reprend le même verrou dans une tâche commandée de la file. Le bundler et les commits interviennent entre vagues, avec inputs stables. Les images/poids exclus du ZIP se restaurent par les scripts existants. Un clone Git seul ne remplace pas les assets non publiés.
