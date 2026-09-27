"""Freeze work-disjoint reference audit/reserve; fetch only audit pages, never reserve.

This is a reference audit, not a new test of a selected geometry candidate.
Original bytes are retained and checked against pinned Git blob identities.
"""
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import random
import urllib.request
import time
from lxml import etree as E
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/loop/reference-a18'
REPO = 'OCR-D/OCR-D-GT-VD-SBB'
SEED = 2026092718


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def freeze(tree):
    books = defaultdict(list)
    entries = {x['path']: x for x in tree['tree']}
    for path in entries:
        if '/OCR-D-GT-PAGE/' in path and path.endswith('.xml'):
            books[path.split('/')[1]].append(path)
    rng = random.Random(SEED)
    chosen = rng.sample(sorted(books), 8)
    pages = []
    for i, book in enumerate(chosen):
        xml = rng.choice(sorted(books[book]))
        img = xml.replace('OCR-D-GT-PAGE', 'OCR-D-IMG').replace('.xml', '.tif')
        pages.append({'work': book, 'role': 'audit' if i < 4 else 'reserve',
                      'xml': xml, 'image': img,
                      'xml_blob': entries[xml]['sha'], 'image_blob': entries[img]['sha']})
    result = {'schema': 'bbvlm.sbb-reference-split/1', 'repository': REPO,
              'revision': tree['sha'], 'seed': SEED, 'selection': 'filenames only; distinct works',
              'created_unix': time.time(), 'pages': pages,
              'reserve_policy': 'no download/inspection until experiment and conventions frozen'}
    path = BASE / 'split.json'
    if path.exists():
        old = json.loads(path.read_text())
        assert old['pages'] == pages and old['revision'] == tree['sha']
        return old
    write(path, result)
    return result


def fetch(args):
    revision, path, blob = args
    dest = BASE / 'source' / path
    if not dest.exists():
        url = f'https://raw.githubusercontent.com/{REPO}/{revision}/{path}'
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    data = dest.read_bytes()
    assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == blob, path
    return {'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'git_blob_verified': True}


def box(node):
    coord = node.find('{*}Coords')
    pts = [tuple(map(float, p.split(','))) for p in coord.get('points').split()]
    return [min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts)]


def txt(node):
    return node.findtext('{*}TextEquiv/{*}Unicode') or ''


def main():
    split = freeze(json.loads((BASE / 'source/tree.json').read_text()))
    jobs = [(split['revision'], p[k], p[k+'_blob']) for p in split['pages']
            if p['role'] == 'audit' for k in ('xml', 'image')]
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(fetch, jobs))
    reports, secret, inputs = [], [], []
    for page in split['pages']:
        if page['role'] != 'audit':
            continue
        root = E.parse(str(BASE / 'source' / page['xml']))
        pn = root.find('.//{*}Page')
        lines = root.findall('.//{*}TextLine')
        words = root.findall('.//{*}Word')
        image = Image.open(BASE / 'source' / page['image']).convert('RGB')
        assert image.size == (int(pn.get('imageWidth')), int(pn.get('imageHeight')))
        empty = sum(not txt(l) for l in lines)
        overlaps = outside = 0
        for line in lines:
            lb = box(line)
            ww = sorted(line.findall('{*}Word'), key=lambda w: box(w)[0])
            for word in ww:
                b = box(word)
                outside += int(b[0] < lb[0] or b[1] < lb[1] or b[2] > lb[2] or b[3] > lb[3])
            for a, b in zip(ww, ww[1:]):
                a, b = box(a), box(b)
                denom = min(a[2]-a[0], b[2]-b[0])
                overlaps += int(denom > 0 and min(a[2], b[2])-max(a[0], b[0]) >= .25*denom)
        reports.append({'work': page['work'], 'lines': len(lines), 'words': len(words),
                        'empty_lines': empty, 'words_outside_line_bbox': outside,
                        'adjacent_overlap_ge_25pct': overlaps,
                        'word_geometry_status': 'present_unadjudicated' if words else 'absent'})
        eligible = [l for l in lines if txt(l)]
        chosen = random.Random(str(SEED)+page['work']).sample(eligible, min(4, len(eligible)))
        for line in chosen:
            token = 'X'+hashlib.sha256((page['xml']+line.get('id')).encode()).hexdigest()[:8]
            b = box(line)
            bounds = [max(0, int(b[0])-3), max(0, int(b[1])-3),
                      min(image.width, int(b[2])+4), min(image.height, int(b[3])+4)]
            dest = BASE / 'input' / f'{token}.png'
            dest.parent.mkdir(parents=True, exist_ok=True)
            image.crop(bounds).save(dest)
            inputs.append({'id': token, 'image': str(dest.relative_to(ROOT))})
            secret.append({'id': token, 'text': txt(line), 'work': page['work'],
                           'line_id': line.get('id'), 'line_bbox': b, 'crop_bbox': bounds,
                           'words': [{'text': txt(w), 'bbox': box(w)} for w in line.findall('{*}Word')]})
    random.Random(SEED).shuffle(inputs)
    write(BASE / 'input/request.json', {'task': 'blind diplomatic OCR', 'items': inputs,
          'instructions': 'Inspect every crop. Preserve spelling, case, punctuation, printed hyphens, long s and diacritics. No editorial repair. One line per id. Return lines [{id,text,uncertain,reason}]. Never read reference/source/other files.'})
    write(BASE / 'private-reference.json', secret)
    write(BASE / 'report.json', {'schema': 'bbvlm.sbb-audit/1', 'pages': reports, 'files': files,
          'sample_lines': len(secret), 'reserve_pages_unopened': 4,
          'runtime_seconds': time.perf_counter()-started,
          'reference_transcription_claim': 'provider GT followed by SBB post-correction/manual page inspection; not perfect truth',
          'cost': {'vlm': 0, 'recognition': 0, 'layout': 0},
          'accepted_for_project_completion_gate': False})
    print(json.dumps({'pages': reports, 'sample_lines': len(secret)}, indent=2))


if __name__ == '__main__':
    main()
