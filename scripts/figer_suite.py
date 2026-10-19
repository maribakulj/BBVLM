#!/usr/bin/env python
"""Sélection indépendante des résultats ; références exclusivement évaluateur."""
from pathlib import Path
import argparse
import hashlib
import json
from collections import Counter


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(destination, home=Path.home()):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination/'evaluation.json'
    if target.exists():
        old = json.loads(target.read_text())
        for row in old['pages']:
            for key in ('image', 'reference'):
                if sha(row[key]) != row[key+'_sha256']:
                    raise ValueError(f'Corpus modifié : {row[key]}')
        return old
    pages = []

    def add(xml, image, family, split, text_gold=True, geometry=True, olr=False):
        if not xml.is_file() or not image.is_file():
            raise FileNotFoundError((xml, image))
        pages.append(dict(id=xml.stem if xml.stem != 'ref.page' else xml.parent.name,
                          family=family, split=split, image=str(image),
                          image_sha256=sha(image), reference=str(xml),
                          reference_sha256=sha(xml), human_text=text_gold,
                          word_geometry=geometry, olr_gold=olr))

    base = home/'Downloads/ATR_TrainingSet_BnF_Newseye_M2+'
    pilots = {'La_Fronde_6703127_T0000003', 'Le_Matin_0576768_T0000002',
              'La_Presse_0545076_T0000002', 'L_OEuvre_4613537_T0000001'}
    for title in ('La_Fronde', 'Le_Matin', 'La_Presse', 'L_OEuvre'):
        candidates = sorted(base.glob(title+'*.xml'))
        dev = [x for x in candidates if x.stem in pilots]
        reserved = [x for x in candidates if x.stem not in pilots][:2]
        if len(dev) != 1 or len(reserved) != 2:
            raise ValueError(f'Suite incomplète : {title}')
        for xml in dev + reserved:
            image = next((xml.with_suffix(e) for e in ('.jpg','.tif','.png')
                          if xml.with_suffix(e).exists()), xml.with_suffix('.jpg'))
            add(xml, image, title, 'dev' if xml in dev else 'reserved')
    ocr = sorted((home/'corpus-vt/raw').glob('*_corrected_*/ref.page.xml'))[:3]
    if len(ocr) != 3:
        raise ValueError('OCR17 incomplet')
    for i, xml in enumerate(ocr):
        add(xml, xml.parent/'image.png', 'OCR17', 'dev' if i == 0 else 'reserved')
    bnl = sorted((home/'Downloads/bnl-ground-truth-newspapers-before-1878-raw').glob('*/*.xml'))
    bnl = [x for x in bnl if x.with_suffix('.png').exists()][:2]
    if len(bnl) != 2:
        raise ValueError('BNL incomplet')
    for xml in bnl:
        add(xml, xml.with_suffix('.png'), 'BNL', 'reserved')
    manifest = home/'axel/data/prepared/olr/newseye_as.json'
    rows = json.loads(manifest.read_text())['pages']
    for title in sorted({r['title'] for r in rows if r['split'] == 'test'}):
        issues = set()
        for row in sorted(rows, key=lambda r:r['page']):
            if row['split'] != 'test' or row['title'] != title or row['issue'] in issues:
                continue
            add(Path(row['xml']), Path(row['image']), 'AS/'+title, 'reserved',
                text_gold=row['human_lines'], geometry=False, olr=True)
            issues.add(row['issue'])
            if len(issues) == 2:
                break
        if len(issues) != 2:
            raise ValueError(f'AS incomplet : {title}')
    seen = set()
    for row in pages:
        if row['image_sha256'] in seen:
            raise ValueError(f'Page dupliquée : {row["id"]}')
        seen.add(row['image_sha256'])
    result = dict(protocol='PROTOCOLE.md v1', protocol_sha256=sha(Path(__file__).resolve().parents[1]/'PROTOCOLE.md'), pages=pages)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    public = dict(protocol=result['protocol'], protocol_sha256=result['protocol_sha256'],
                  pages=[{k:r[k] for k in ('id','family','split','image','image_sha256')} for r in pages])
    (destination/'production.json').write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('destination'); args=ap.parse_args()
    m=freeze(args.destination)
    print(json.dumps(dict(pages=len(m['pages']), families=dict(Counter(r['family'] for r in m['pages'])), splits=dict(Counter(r['split'] for r in m['pages']))), ensure_ascii=False))
