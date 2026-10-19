#!/usr/bin/env python
"""Page de presse → plan automatique → Gemini → image/ALTO et évaluation.

Relancer exactement la même commande reprend les journaux de transcription.
Les références ne sont ouvertes que par le processus d'évaluation final.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from page_anchors import save_json,sha256
from page_layout_auto import write_plan
from page_pipeline import run,KRAKEN_PYTHON
from transcrire_regions import prepare,transcribe


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image');parser.add_argument('automatic_lines',help='Dossier automatique existant, ou auto pour segmenter les pixels');parser.add_argument('output')
    parser.add_argument('--gemini-pane',required=True)
    parser.add_argument('--evaluation-manifest')
    parser.add_argument('--timeout',type=int,default=900)
    parser.add_argument('--minimum-text-coverage',type=float,default=.97)
    parser.add_argument('--no-region-constraint',action='store_true',help='Appariement ancien, sans contrainte de région')
    parser.add_argument('--max-region-height',type=int,default=1500,help='0 = colonnes entières')
    parser.add_argument('--no-block-ctc',action='store_true',help='Sans découpage du texte entre lignes par vraisemblance CTC')
    args=parser.parse_args()
    image=Path(args.image).resolve();output=Path(args.output).resolve()
    source=output/'segmentation' if args.automatic_lines=='auto' else Path(args.automatic_lines).resolve()
    def state(stage,**kwargs):save_json(output/'state.json',dict(stage=stage,**kwargs))
    try:
        if args.automatic_lines=='auto':
            state('automatic_segmentation')
            subprocess.run([str(KRAKEN_PYTHON),str(ROOT/'scripts/segmenter_page.py'),str(image),str(source)],check=True)
        state('layout')
        saved_plan=output/'layout/plan.json'
        if saved_plan.exists():
            plan=json.loads(saved_plan.read_text())
            if plan['image_sha256']!=sha256(image):raise ValueError('Le plan sauvegardé appartient à une autre image')
        else:
            plan=write_plan(image,source,output/'layout')
        if args.max_region_height and plan.get('parameters',{}).get('max_region_height')!=args.max_region_height:
            # Colonnes hautes découpées aux blancs entre lignes : réponses Gemini
            # plus courtes, que le flux d'agy ne coupe pas.
            from region_split import split_tall_regions
            plan=split_tall_regions(plan,json.loads((source/'segmentation.json').read_text()),args.max_region_height)
            save_json(saved_plan,plan)
        if 'dropped_contained_regions' not in plan.get('audit',{}):
            # Région contenue dans une autre : lue deux fois, lignes sans région.
            from region_split import drop_contained_regions
            plan=drop_contained_regions(plan,json.loads((source/'segmentation.json').read_text()))
            plan.setdefault('audit',{}).setdefault('dropped_contained_regions',[])
            save_json(saved_plan,plan)
        manifest=prepare(image,plan,output/'transcription')
        state('gemini',layout_audit=plan['audit'])
        transcribe(manifest,output/'transcription',args.gemini_pane,args.timeout)
        state('geometry',layout_audit=plan['audit'])
        text=output/'transcription';inspection=output/'inspection'
        report=run(image,text/'vt.gemini.md',text/'vt-provenance.json',source,inspection,
                   anchor_reader='ctc',repair_ownership=True,
                   region_plan=None if args.no_region_constraint else output/'layout/plan.json',
                   block_ctc=not args.no_block_ctc)
        geometry=json.loads((inspection/'geometry-report.json').read_text())
        if geometry['statuses'].get('alignement_non_resolu',0) or (report['text_coverage']['fraction'] or 0)<args.minimum_text_coverage:
            state('boundary_recovery')
            from page_boundary_recovery import recover
            refined=output/'inspection-refined'
            refined_report=recover(image,inspection,refined,KRAKEN_PYTHON)
            if (refined_report['text_coverage']['fraction'] or 0)>=(report['text_coverage']['fraction'] or 0):
                report=refined_report;inspection=refined
        files={'image':inspection/image.name,'alto':inspection/'page.alto.xml',
               'markdown':inspection/'vt.gemini.md','layout':output/'layout/plan-preview.jpg',
               'export_report':inspection/'page-export.json',
               'ownership_audit':inspection/'ownership-audit.json'}
        if args.evaluation_manifest:
            state('independent_evaluation')
            cer=inspection/'cer-hipe.json'
            subprocess.run([sys.executable,str(ROOT/'scripts/evaluer_ocr_page.py'),
                            args.evaluation_manifest,str(text),str(cer)],check=True)
            files['cer_hipe']=cer
            subprocess.run([sys.executable,str(ROOT/'scripts/evaluer_regions.py'),
                            args.evaluation_manifest,str(text)],check=True)
            files['cer_regions']=text/'cer-regions-diagnostic.json'
            # Rapport complet des écarts Gemini ↔ VT, à chaque passe.
            sys.path.insert(0,str(ROOT/'scripts'))
            from rapport_differences import build
            verifications=output/'verifications-visuelles.json'
            differences_summary=build(args.evaluation_manifest,text,inspection,output/'differences',title=image.stem,
                                      verifications=verifications if verifications.exists() else None)
            files['differences']=output/'differences'/'differences.html'
        metadata=json.loads((text/'vt-provenance.json').read_text())
        delivery=dict(files={k:str(p) for k,p in files.items()},
                      sha256={k:sha256(p) for k,p in files.items()},
                      layout_audit=plan['audit'],text_coverage=report['text_coverage'],
                      interrupted_regions=metadata.get('interrupted_regions',[]),
                      empty_regions=metadata.get('empty_regions',[]),
                      reading_certified=False,geometry_certified=False,
                      pipeline_completed=True,
                      text_coverage_gate=dict(minimum=args.minimum_text_coverage,
                                              passed=(report['text_coverage']['fraction'] or 0)>=args.minimum_text_coverage),
                      status='exported_with_audits_pending_review')
        if 'cer_hipe' in files:
            full=json.loads(files['cer_hipe'].read_text())['text']['hipe_ocrepair_2026']
            spatial=json.loads(files['cer_regions'].read_text())
            delivery['cer_hipe']=dict(reference_xml_order=full,
                common_spatial_order=spatial.get('whole_page_same_spatial_reference_order',{}).get('regions'),
                regional_diagnostic=dict(cer=spatial['cer'],completed=spatial['completed'],total=spatial['total'],
                                         unassigned_reference_lines=spatial['unassigned_reference_lines']))
        if 'differences' in files:
            delivery['differences_gemini_vt']=dict(total=differences_summary['differences'],by_category=differences_summary['by_category'])
        save_json(output/'livraison.json',delivery)
        state('exported',delivery=delivery)
        print(json.dumps(delivery,ensure_ascii=False,indent=2))
    except Exception as exc:
        state('interrupted',error=f'{type(exc).__name__}: {exc}',resume='Relancer la même commande ; ne pas effacer les journaux.')
        raise


if __name__=='__main__':main()
