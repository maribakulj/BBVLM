#!/usr/bin/env python
"""Tableau des erreurs de deux lecteurs (Haiku, Gemini) face à la VT, ligne par ligne.

Chaque ligne de la VT est appariée à la ligne la plus proche de chaque lecture ;
les mots sont comparés après la normalisation du CER côté VT (casse,
ponctuation, apostrophes, s long ignorés). Une ligne du tableau = un passage où
au moins un lecteur s'écarte de la VT, avec le verdict : erreur de Haiku seul,
de Gemini seul, des deux (même lecture ou non). La VT elle-même peut être
fautive : la colonne « mêmes lectures » le signale souvent.
Évaluation seulement : la VT n'entre jamais dans la chaîne.
"""
import argparse
import difflib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from cer_vt import cer_vt, markdown_text
from page_reference_text import load_page_reference
from rapidfuzz import fuzz, process


def norm_words(text):
    return [w for w in (cer_vt(w.replace('¬', '-')) for w in text.split()) if w]


def same(a, b):
    """Égaux pour le CER côté VT, espaces compris ignorés (« LATEMPÉRATURE » = « LA TEMPÉRATURE »)."""
    return ''.join(norm_words(a)) == ''.join(norm_words(b))


def table_rows(markdown):
    """Tableaux Markdown (« | a | b | ») ramenés à des lignes de texte (« a b ») ;
    lignes de séparation retirées. Sinon une ligne de tableau ne s'apparie à rien."""
    out = []
    for line in markdown.splitlines():
        if line.lstrip().startswith('|'):
            if set(line.strip()) <= set('|-: '):
                continue
            line = ' '.join(c.strip() for c in line.strip().strip('|').split('|'))
        out.append(line)
    return '\n'.join(out)


def best_lines(reference, hypothesis):
    """Pour chaque ligne de VT, la ligne de lecture la plus proche (ou '')."""
    keys = [cer_vt(h) for h in hypothesis]
    out = []
    for line in reference:
        found = process.extractOne(cer_vt(line), keys, scorer=fuzz.ratio, score_cutoff=55)
        out.append(hypothesis[found[2]] if found else '')
    return out


def spans(ref_words, hyp_words):
    """[(i1, i2, mots lus)] : passages de la VT (indices de mots) lus autrement."""
    a, b = [cer_vt(w.replace('¬', '-')) for w in ref_words], [cer_vt(w.replace('¬', '-')) for w in hyp_words]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != 'equal':
            out.append((i1, i2, ' '.join(hyp_words[j1:j2])))
    return out


def compare(reference_xml, readings):
    rows, _ = load_page_reference(reference_xml)
    reference = [r['text'] for r in rows if r['text'].strip()]
    matched = {}
    for name, path in readings.items():
        text = markdown_text(table_rows(Path(path).read_text()))[0]
        matched[name] = best_lines(reference, [l for l in text.splitlines() if l.strip()])
    names = list(readings)
    table, counts = [], {'haiku_seul': 0, 'gemini_seul': 0, 'les_deux_meme_lecture': 0,
                         'les_deux_lectures_differentes': 0, 'mots_vt': 0}
    for k, line in enumerate(reference):
        ref_words = line.split()
        counts['mots_vt'] += len(ref_words)
        found = {n: spans(ref_words, matched[n][k].split()) for n in names}
        # Regrouper les passages qui se recouvrent (ou se touchent) entre lecteurs.
        marks = sorted((i1, max(i2, i1 + 1), n, got) for n in names for i1, i2, got in found[n])
        clusters = []
        for i1, i2, n, got in marks:
            if clusters and i1 <= clusters[-1]['i2']:
                c = clusters[-1]; c['i2'] = max(c['i2'], i2); c[n].append(got)
            else:
                clusters.append({'i1': i1, 'i2': i2, **{m: [] for m in names}, n: [got]})
        for c in clusters:
            vt = ' '.join(ref_words[c['i1']:c['i2']])
            reads = {n: ' '.join(c[n]) if c[n] else '=' for n in names}
            # Écart de ponctuation ou d'espace seulement : ignoré, comme dans le CER côté VT.
            wrong = [n for n in names if c[n] and not same(vt, reads[n])]
            if not wrong:
                continue
            reads = {n: reads[n] if n in wrong else '=' for n in names}
            if len(wrong) == 1:
                verdict = wrong[0] + '_seul'
            elif same(reads[names[0]], reads[names[1]]):
                verdict = 'les_deux_meme_lecture'
            else:
                verdict = 'les_deux_lectures_differentes'
            counts[verdict] += 1
            table.append(dict(ligne=k + 1, vt=vt or '∅', **reads, verdict=verdict,
                              contexte=line))
    return table, counts


VERDICTS = {'haiku_seul': 'Haiku seul faux', 'gemini_seul': 'Gemini seul faux',
            'les_deux_meme_lecture': 'les deux, même lecture (VT douteuse ?)',
            'les_deux_lectures_differentes': 'les deux, lectures différentes'}


def markdown(page, table, counts):
    out = [f'# {page} — Haiku contre Gemini, face à la VT', '',
           f"Mots de la VT : {counts['mots_vt']} · passages en écart : {len(table)}", '',
           '| Verdict | Passages |', '|---|---|']
    out += [f'| {VERDICTS[k]} | {counts[k]} |' for k in VERDICTS]
    for key, title in VERDICTS.items():
        rows = [r for r in table if r['verdict'] == key]
        if not rows:
            continue
        out += ['', f'## {title} ({len(rows)})', '', '| Ligne VT | VT | Haiku | Gemini |', '|---|---|---|---|']
        out += [f"| {r['ligne']} | {r['vt']} | {r['haiku']} | {r['gemini']} |".replace('\n', ' ') for r in rows]
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference'); parser.add_argument('haiku'); parser.add_argument('gemini')
    parser.add_argument('--page', default='page'); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    table, counts = compare(args.reference, {'haiku': args.haiku, 'gemini': args.gemini})
    Path(args.output).write_text(markdown(args.page, table, counts), encoding='utf-8')
    Path(args.output).with_suffix('.json').write_text(json.dumps(dict(counts=counts, rows=table), ensure_ascii=False, indent=1))
    print(json.dumps(counts, ensure_ascii=False))
