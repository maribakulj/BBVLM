"""Point d'entrée de la chaîne BBVLM (boucle) : image de page → ALTO 4.4 + index.

Étapes (les deux marquées VLM sont faites par des lecteurs Opus, hors de ce
script, sur les fichiers qu'il prépare) :
  prepare DOSSIER      vues (page, bandes, moitiés ×1,6) + segmentation kraken
  [VLM] deux lectures indépendantes → DOSSIER/lu_a.txt, DOSSIER/lu_b.txt
                        (consigne outils/consigne_P5.md)
  arbitrage DOSSIER    p2 (OCR-D, R1, R2) sur A et B, lignes resserrées,
                        recadrage des seules lignes en désaccord → DOSSIER/p3/taches.json
  [VLM] arbitre → DOSSIER/p3/verdicts.json
  final DOSSIER        texte P3 → ALTO (blocs typés, ReadingOrder, lignes non
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
        with open(f'{d}/p2_{n}.txt', 'w') as f:
            subprocess.run([PY, 'p2.py', f'{d}/lu_{n}.txt'], check=True, cwd=ICI, stdout=f)
    run('serre.py', d)
    run('p3.py', 'prepare', d)


def final(d):
    if not os.path.exists(f'{d}/p3/verdicts.json'):
        open(f'{d}/p3/verdicts.json', 'w').write('[]')
    run('p3.py', 'fusionne', d)
    run('vers_alto.py', d, f'{d}/p3_final.txt', f'{d}/page.alto.xml', f'{d}/lu_a.txt')


if __name__ == '__main__':
    {'prepare': prepare, 'arbitrage': arbitrage, 'final': final}[sys.argv[1]](sys.argv[2].rstrip('/'))
