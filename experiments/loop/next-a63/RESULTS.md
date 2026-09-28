# A63 — vraie lecture enchaînée après A62

La file a enchaîné préparation, crops, réservation du lecteur réel et scoring. Un Sol neuf a inspecté les12 vues de6 lignes (4résidus A61,2témoins). Aucun texte candidat/référence n'était fourni. Source et XML inchangés ; empreintes, inventaire et IDs validés.

Sur ces seules lignes choisies après les scores : **accord lexical6/171→4/171 éditions**, soit3,51→2,34%, lignes exactes2→4. `search_v1` reste6/223, car deux variations de ponctuation/espacement compensent les deux gains lexicaux. Les témoins restent exacts lexicalement mais changent en strict/recherche : un point devient ♦ et un espace apparaît avant ;. Ne pas fusionner ces scores ni fabriquer un CER de bloc réparé.

| Ligne | Référence | A61 | A63 | Interprétation |
|---|---|---|---|---|
| R902 | erân | erôn | erân | Gain d'accord ; image relue par parent, compatible avec â. |
| R563 | Gróss | Gròss | Gróss | Gain d'accord ; le lecteur signale encore le flou de l'accent. |
| R816 | fiée | flée | flée | Image native et agrandie relues : forme compatible avec l, erreur de référence probable ; pas adjudication indépendante. |
| R729 | kernt / ganzt | kemt / ganet | kemt / ganst | m visible compatible avec kemt ; graphie suivante reste instable entre trois lectures. Pas de correction automatique de GT. |

La résolution de présentation peut aider, mais ce diagnostic change aussi de session et utilise une sélection et géométrie oracle. Il ne prouve ni causalité isolée, ni un routeur déployable, ni perfection. Coût :1session Sol,6crops uniques/12vues, aucun nouveau forward OCR/PERO, tokens/prix non exposés.

Claude relu : head76056c5c1957e0de4232f0aef1f6cbc7f2893402, journalI01 inchangé et code inflexion.py lu. Revue primaire et limites disponibles dans PAPER_SUMMARIES.md. Aucun modèle lourd installé.

Décision : arrêter le réglage sur0455, conserver le dossier d'adjudication et figer une nouvelle validation diverse pour un mécanisme de reprise ciblée observable sans GT. Pendant l'attente d'une adjudication humaine, avancer une piste distincte de géométrie/OLR ou benchmark normalisé HIPE. Le runner ne certifie aucun gate scientifique.
