#!/usr/bin/env python
"""Commande unique de production, étapes reprises par empreintes et requêtes IDs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
from lecture import HerdrGeminiReader, ReaderUnavailable, ReaderQuotaExceeded
from produire import produire
from olr import infer
from export_training import export
from verify_words import restore_checked_annotations


LAYOUT_PYTHON=Path.home()/'outils-seg/layout-env/bin/python'


def run(image, directory, pane, model=None, segmentation='auto', batch_size=10,reading_revision='v1',
        layout='auto',layout_python=None,line_refinement='none',reading_input='legacy',word_boundaries='auto',char_alignment='auto',word_verification='auto'):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(Path(__file__).parent/'boxers'))
    from forcectc import ForceCTC,CHEMIN,FALLBACK
    config=directory/'pipeline-config.json'
    previous=json.loads(config.read_text()) if config.exists() else None
    # Les anciens essais gardent leur configuration et restent comparables.
    # Une nouvelle page active la détection non textuelle par défaut.
    if layout=='auto':layout=previous.get('layout','none') if previous else 'ppdl3'
    if word_boundaries=='auto':word_boundaries=previous.get('word_boundaries','midpoint') if previous else 'ink'
    if char_alignment=='auto':char_alignment=previous.get('char_alignment','line') if previous else 'word'
    if word_verification=='auto':word_verification=previous.get('word_verification','none') if previous else 'blind'
    key=dict(image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),
             model_sha256=hashlib.sha256(Path(model or CHEMIN).read_bytes()).hexdigest(),
             fallback_sha256=hashlib.sha256(Path(FALLBACK).read_bytes()).hexdigest() if Path(FALLBACK).exists() else None,
             segmentation=segmentation,batch_size=batch_size,reading_revision=reading_revision,
             layout=layout,version='pipeline-v1')
    if line_refinement!='none':key['line_refinement']=line_refinement
    if reading_input!='legacy':key['reading_input']=reading_input
    if word_boundaries!='midpoint':key['word_boundaries']=word_boundaries
    if char_alignment!='line':key['char_alignment']=char_alignment
    if word_verification!='none':key['word_verification']=word_verification
    if previous:
        previous.setdefault('reading_revision','v1');previous.setdefault('layout','none')
        if previous != key:
            raise ValueError('Configuration modifiée : choisir un nouveau dossier pour conserver les anciens essais')
    config.write_text(json.dumps(key,indent=2))
    state=directory/'pipeline-state.json'
    def checkpoint(stage,**extra):
        tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(dict(stage=stage,**extra),ensure_ascii=False,indent=2));tmp.replace(state)
    try:
        layout_data=None
        if layout=='ppdl3':
            checkpoint('image_layout')
            candidate_file=directory/'layout-candidates.json'
            if candidate_file.exists():
                layout_data=json.loads(candidate_file.read_text())
                if layout_data['image_sha256']!=key['image_sha256']:
                    raise ValueError('Candidats de mise en page issus d’une autre image')
            else:
                subprocess.run([str(layout_python or LAYOUT_PYTHON),str(Path(__file__).parent/'bb_layout.py'),
                                str(image),str(candidate_file)],check=True)
                layout_data=json.loads(candidate_file.read_text())
        if not (directory/'annotations.json').exists() or not (directory/'provenance.json').exists():
            checkpoint('reading_and_geometry')
            produire(str(image),directory,HerdrGeminiReader(pane,directory/'lecture-jobs',revision=reading_revision,input_style=reading_input),
                     ForceCTC(model,boundary_mode=word_boundaries,char_alignment=char_alignment),par_bloc=batch_size,segmentation_strategy=segmentation,
                     line_refinement=line_refinement)
        else:
            print('Transcriptions/géométrie sauvegardées : reprise sans nouvelle lecture',flush=True)
        if word_verification=='blind':
            checkpoint('intrinsic_word_verification')
            from verify_words import verify
            record=directory/'word-verification.json';annotations_file=directory/'annotations.json'
            if record.exists():
                checked=json.loads(record.read_text())
                if checked['image_sha256']!=key['image_sha256']:raise ValueError('Vérification de mots issue d’une autre image')
                restore_checked_annotations(annotations_file,checked)
            else:
                before=annotations_file.read_bytes()
                checked=verify(image,json.loads(before),pane,directory/'word-verification-jobs')
                content=json.dumps(checked['annotations'],ensure_ascii=False,indent=2).encode()
                checked.update(image_sha256=key['image_sha256'],input_annotations_sha256=hashlib.sha256(before).hexdigest(),
                               output_annotations_sha256=hashlib.sha256(content).hexdigest())
                tmp=record.with_suffix('.tmp');tmp.write_text(json.dumps(checked,ensure_ascii=False,indent=2));tmp.replace(record)
                tmp=annotations_file.with_suffix('.tmp');tmp.write_bytes(content);tmp.replace(annotations_file)
        if not (directory/'olr.json').exists():
            checkpoint('olr')
            annotations=json.loads((directory/'annotations.json').read_text())
            regions=[];text_geometry=[]
            if layout_data:
                from bb_layout import nontext_regions,text_regions
                regions=nontext_regions(layout_data)
                text_geometry=text_regions(layout_data)
            result=infer(image,annotations,pane,directory/'olr-jobs',regions=regions,text_regions=text_geometry)
            (directory/'olr.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        checkpoint('export')
        result=export(image,directory)
        checkpoint('exported_pending_independent_evaluation',report=result,criteria_met=False)
        return result
    except ReaderQuotaExceeded as exc:
        checkpoint('waiting_for_native_quota',error=str(exc),retry_at=exc.retry_at,
                   evidence=exc.evidence,resubmit=False)
        raise
    except ReaderUnavailable as exc:
        checkpoint('waiting_for_existing_gemini_job',error=str(exc),resubmit=False)
        raise


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('directory');ap.add_argument('--gemini-pane',required=True)
    ap.add_argument('--ctc-model');ap.add_argument('--segmentation',choices=('full','tiles','auto','auto-v2'),default='auto')
    ap.add_argument('--batch-size',type=int,default=10)
    ap.add_argument('--reading-revision',default='v1')
    ap.add_argument('--layout',choices=('auto','none','ppdl3'),default='auto')
    ap.add_argument('--layout-python')
    ap.add_argument('--line-refinement',choices=('none','ink'),default='none')
    ap.add_argument('--reading-input',choices=('legacy','lines','sheets'),default='legacy')
    ap.add_argument('--word-boundaries',choices=('auto','midpoint','ink','ink_clean','ink_clean_baseline','ink_clean_local'),default='auto')
    ap.add_argument('--char-alignment',choices=('auto','line','word'),default='auto')
    ap.add_argument('--word-verification',choices=('auto','none','blind'),default='auto');args=ap.parse_args()
    print(json.dumps(run(args.image,args.directory,args.gemini_pane,args.ctc_model,args.segmentation,args.batch_size,args.reading_revision,
                         args.layout,args.layout_python,args.line_refinement,args.reading_input,args.word_boundaries,args.char_alignment,args.word_verification),ensure_ascii=False))
