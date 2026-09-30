"""Point d'entrée de la chaîne BBVLM (boucle) : image de page → ALTO 4.4 + index.

Étapes (les deux marquées VLM sont faites par des lecteurs Opus, hors de ce
script, sur les fichiers qu'il prépare) :
  prepare DOSSIER      vues (page, bandes, moitiés ×1,6) + segmentation kraken
  [VLM] deux lectures indépendantes → DOSSIER/lu_a.txt, DOSSIER/lu_b.txt
        (mode économe : lu_a seule ; O10-O13 : 126-131 éditions contre 122, −50 % de lecture)
                        (consigne outils/consigne_P6e.md (P6 + abréviations O21b + deux blocs = deux lignes O22))
  arbitrage DOSSIER    p2 (OCR-D, R1, R2) sur A et B, lignes resserrées,
                        recadrage des seules lignes en désaccord → DOSSIER/p3/taches.json
  [VLM] arbitre (outils/consigne_arbitre_P3.md) → DOSSIER/p3/verdicts.json
        et, dans le même appel, signe d'inflexion (consigne_inflexion.md) → DOSSIER/inflexion/verdicts.json
  final DOSSIER        texte P3 → ALTO (W03b : si BBVLM_CALA_PY désigne le python de
                        l'environnement Calamari, pré-calcul calamari_bin.json des lignes en romain)
                        (blocs typés, ReadingOrder, lignes non
                        placées marquées) validé XSD → DOSSIER/page.alto.xml
Aucune étape ne lit une référence. Les évaluations (cer, bilan_adj, olr,
eval_alto, critere_final, recherche) sont des outils séparés.
"""
import os, subprocess, sys
ICI = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(*a):
    subprocess.run([PY, *a], check=True, cwd=ICI)


def prepare(d, kraken_py=os.environ.get('BBVLM_KRAKEN_PY', PY)):
    os.makedirs(f'{d}/vues', exist_ok=True)
    run('vues_zoom.py', d)
    subprocess.run([kraken_py, 'segmente.py', d], check=True, cwd=ICI)


def arbitrage(d):
    for n in 'ab':
        if not os.path.exists(f'{d}/lu_{n}.txt'): continue     # mode économe : lecture A seule
        with open(f'{d}/p2_{n}.txt', 'w') as f:
            subprocess.run([PY, 'p2.py', f'{d}/lu_{n}.txt'], check=True, cwd=ICI, stdout=f)
    run('serre.py', d)
    run('p3.py', 'prepare', d)
    run('inflexion.py', 'prepare', d)      # I01 : même appel d'arbitre que P3


def final(d):
    if not os.path.exists(f'{d}/p3/verdicts.json'):
        open(f'{d}/p3/verdicts.json', 'w').write('[]')
    run('p3.py', 'fusionne', d)
    run('inflexion.py', 'applique', d)     # sans verdicts ou sans décision nette : texte P3 inchangé
    run('vers_alto.py', d, f'{d}/p3i_final.txt', f'{d}/page.alto.xml', f'{d}/lu_a.txt')


if __name__ == '__main__':
    {'prepare': prepare, 'arbitrage': arbitrage, 'final': final}[sys.argv[1]](sys.argv[2].rstrip('/'))
