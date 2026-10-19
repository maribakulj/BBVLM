#!/usr/bin/env python
"""Contrats d'export réels Kraken PAGE/ALTO et IR Axel ; aucune référence."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import sys
import unicodedata
from kraken.lib.xml import XMLPage


def verify(directory,axel_root):
    directory=Path(directory);sys.path.insert(0,str(Path(axel_root)/'src'))
    from axel.pipeline.ir import page_from_dict,page_to_dict
    raw=json.loads((directory/'axel-ir.json').read_text());page=page_from_dict(raw)
    if page_to_dict(page)!=raw:raise ValueError('IR Axel aller-retour modifie les données')
    rows=[json.loads(s) for s in (directory/'training.jsonl').read_text().splitlines()]
    expected=[(r['line_id'],r['text']) for r in rows]
    if [(line.id,line.text) for line in page.lines()]!=expected:
        raise ValueError('IR/JSONL texte ou ordre différent')
    for row in rows:
        if row['page_id']!=page.id or row['text']!=unicodedata.normalize('NFC',row['text']):
            raise ValueError('ID page ou NFC incorrect')
        if row['chars'] and len(row['chars'])!=len(row['text']):raise ValueError('Texte/positions incohérents')
        for word in row['words']:
            if row['text'][word['start']:word['end']]!=word['text']:raise ValueError('Offsets de mots incohérents')
    counts={}
    for mode,filename in [('alto','training.alto.xml'),('page','training.page.xml')]:
        parsed=XMLPage(str(directory/filename),filetype=mode)
        actual=[(line.id,line.text) for line in parsed.get_sorted_lines()]
        if actual!=expected:raise ValueError(f'Kraken {mode} omet/modifie texte, IDs ou ordre')
        counts[mode]=len(actual)
    if not Path(page.image).is_file():raise ValueError('Image de training absente')
    return dict(kraken_version=importlib.metadata.version('kraken'),page_id=page.id,
                page_lines=counts['page'],alto_lines=counts['alto'],texts_exact=True,image_resolves=True,
                axel_ir_roundtrip=True,axel_ir_lines=len(page.lines()),
                nfc_characters=sum(len(r['chars']) for r in rows),scope='reader compatibility; not independent quality certification')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory');ap.add_argument('--axel-root',default=str(Path.home()/'axel'))
    args=ap.parse_args();result=verify(args.directory,args.axel_root)
    (Path(args.directory)/'reader-integration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False))
