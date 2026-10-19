#!/usr/bin/env python
"""Suite publique entière → Markdown ; les échecs restent dans l'état de reprise."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lecture import ReaderUnavailable, ReaderQuotaExceeded
from page_markdown import PageMarkdownReader
from page_native_markdown import NativeMarkdownReader
from page_paged_markdown import PagedMarkdownReader
from page_minimal_markdown import MinimalMarkdownReader


def save(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2))
    temporary.replace(path)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('manifest');ap.add_argument('outputs')
    ap.add_argument('--split',choices=('dev','reserved','all'),default='all')
    ap.add_argument('--gemini-pane',required=True)
    ap.add_argument('--timeout',type=int,default=900)
    ap.add_argument('--wait-native-quota',action='store_true')
    ap.add_argument('--native-markdown',action='store_true')
    ap.add_argument('--paged-markdown',action='store_true')
    ap.add_argument('--minimal-markdown',action='store_true')
    ap.add_argument('--wait-native-recovery',action='store_true')
    ap.add_argument('--tile-size',type=int,default=1536)
    args=ap.parse_args()
    if sum([args.paged_markdown,args.native_markdown,args.minimal_markdown])>1:ap.error('Choisir un seul protocole Markdown')
    manifest=json.loads(Path(args.manifest).read_text())
    allowed={'id','family','split','image','image_sha256'}
    if any(set(r)!=allowed for r in manifest['pages']):
        raise ValueError('Production : seules les images publiques sont autorisées')
    root=Path(args.outputs);root.mkdir(parents=True,exist_ok=True)
    selected=[r for r in manifest['pages'] if args.split=='all' or r['split']==args.split]
    # Dev d'abord, puis TOUTES les réservées ; aucun tri par qualité mesurée.
    selected.sort(key=lambda r: r['split']!='dev')
    state=root/'driver-state.json'
    for row in selected:
        if hashlib.sha256(Path(row['image']).read_bytes()).hexdigest()!=row['image_sha256']:
            raise ValueError('Image modifiée : '+row['id'])
        output=root/row['id']
        reader=(MinimalMarkdownReader(args.gemini_pane,output/'page-lecture-jobs',args.timeout) if args.minimal_markdown else
                PagedMarkdownReader(args.gemini_pane,output/'page-lecture-jobs',args.timeout) if args.paged_markdown else
                NativeMarkdownReader(args.gemini_pane,output/'page-lecture-jobs',args.timeout,args.tile_size)
                if args.native_markdown else PageMarkdownReader(args.gemini_pane,output/'page-lecture-jobs',args.timeout))
        while True:
            save(state,dict(stage='reading_whole_page',page=row['id'],split=row['split'],pages=len(selected)))
            try:
                reading=reader.read_page(row['image'],output)
                break
            except ReaderQuotaExceeded as exc:
                save(state,dict(stage='waiting_for_native_quota',page=row['id'],retry_at=exc.retry_at,
                                evidence=exc.evidence,blind_timeout_retry=False,pages=len(selected)))
                if not args.wait_native_quota:raise
                while time.time()<exc.retry_at:time.sleep(min(30,exc.retry_at-time.time()))
            except ReaderUnavailable as exc:
                save(state,dict(stage='recover_existing_job_before_new_submission',page=row['id'],
                                error=str(exc),blind_timeout_retry=False,pages=len(selected)))
                if args.wait_native_recovery:
                    # Un timeout ne déclenche aucun prompt : le passage suivant
                    # récupère le même job/cache seulement après la fin native.
                    import subprocess
                    native=subprocess.run(['herdr','agent','get',args.gemini_pane],
                                          capture_output=True,text=True,timeout=10)
                    try:agent=json.loads(native.stdout)['result']['agent']
                    except (ValueError,KeyError):raise exc
                    if agent.get('agent') in ('agy','gemini') and agent.get('agent_status')=='working':
                        time.sleep(15)
                        continue
                raise
        print(json.dumps(dict(page=row['id'],characters=len(reading.text),uncertain=reading.uncertain,
                              job_id=reading.job_id,stage='vt_saved_before_geometry')),flush=True)
    save(state,dict(stage='completed_pending_independent_evaluation',pages=len(selected),criteria_met=False))
