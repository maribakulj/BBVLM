# O07 — chaîne P3 : deux passes, arbitrage des désaccords seulement

Fixé le 2026-09-28 d'après les statistiques d'accord d'O04-O06 (303 lignes où
deux passes concordent : 95 % justes ; 13 % de lignes en désaccord), **avant
tout score sur O07**. Pages : suite du tirage (AphoqvSuS_88125679X/20,
albedm_837425875/31, 730277879_82603893X_1795000200/190, berirev_867083778/49).

P3, sans aucune référence :
1. deux passes Opus P2 indépendantes (A, B) ;
2. appariement des lignes A/B ; lignes identiques gardées telles quelles ;
3. segmentation kraken, resserrement G03, alignement lecture → lignes
   (`aligne.py`, ordre par colonnes à recouvrement horizontal) ;
4. chaque ligne en désaccord est recadrée à partir de SA ligne kraken et
   soumise à un arbitre Opus (X/Y aléatoires) ; son texte remplace celui de A.

Coût : 2 passes page + 1 passe sur les seules lignes en désaccord.
Mesure : CER diplo de A, B et P3 contre la référence distribuée, puis contre la
référence doublement adjugée par des arbitres **distincts** de celui de P3.
Hypothèse : P3 ≤ min(A, B) sur chaque page.
