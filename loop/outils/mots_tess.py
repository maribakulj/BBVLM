"""W01 — bords de mots par Tesseract (ancrage au mot, L10).

Tesseract lit la ligne (psm 7, TSV) et donne une boîte par mot. Les mots de
la lecture sont appariés aux mots Tesseract par alignement de séquences
(distance d'édition sur la vue réduite) ; un mot apparié avec une distance
normalisée ≤ SEUIL reçoit les bords gauche/droit de Tesseract (la hauteur
reste celle du calcul connexe). Les autres gardent leur boîte.
Cache : DOSSIER/mots_tesseract.json (clé = boîte de ligne).
"""
import json, os, subprocess
import cv2
from ancre import TESSDATA, reduit
from cer import lev

SEUIL = float(os.environ.get('BBVLM_W01_SEUIL', '0.34'))


def mots_ligne(gray, box, lang, cache, k):
    if k in cache: return cache[k]
    x0, y0, x1, y1 = (int(v) for v in box)
    crop = gray[max(0, y0-4):y1+5, max(0, x0-4):x1+5]
    out = []
    if crop.size:
        ok, png = cv2.imencode('.png', crop)
        r = subprocess.run(['tesseract', 'stdin', 'stdout', '--tessdata-dir', TESSDATA, '-l', lang, '--psm', '7', '-c', 'tessedit_create_tsv=1'],
                           input=png.tobytes(), capture_output=True, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
        for l in r.stdout.decode('utf-8', 'replace').splitlines()[1:]:
            c = l.split('\t')
            if len(c) == 12 and c[0] == '5' and c[11].strip():
                L, T, W, H = map(int, c[6:10])
                out.append([c[11], max(0, x0-4)+L, max(0, x0-4)+L+W-1])
    cache[k] = out
    return out


def aligne(nous, eux):
    """Appariement monotone mot à mot (programmation dynamique)."""
    A = [reduit(w) for w in nous]; B = [reduit(w[0]) for w in eux]
    n, m = len(A), len(B)
    D = [[0.0]*(m+1) for _ in range(n+1)]; P = [[None]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1): D[i][0] = i; P[i][0] = 'h'
    for j in range(1, m+1): D[0][j] = j; P[0][j] = 'g'
    for i in range(1, n+1):
        for j in range(1, m+1):
            d = lev(A[i-1], B[j-1]) / max(1, len(A[i-1]), len(B[j-1]))
            D[i][j], P[i][j] = min((D[i-1][j-1]+d, 'd'), (D[i-1][j]+1, 'h'), (D[i][j-1]+1, 'g'))
    res, i, j = {}, n, m
    while i > 0 and j > 0:
        if P[i][j] == 'd':
            d = lev(A[i-1], B[j-1]) / max(1, len(A[i-1]), len(B[j-1]))
            if d <= SEUIL and len(A[i-1]) >= 1: res[i-1] = j-1
            i, j = i-1, j-1
        elif P[i][j] == 'h': i -= 1
        else: j -= 1
    return res
