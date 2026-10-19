#!/usr/bin/env python
"""Copier la paire image/ALTO et ses mesures vérifiées pour l'inspecteur."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
import alto
from lxml import etree
from page_anchors import save_json,sha256
from page_region_audit import coverage


def deliver(run,destination,inspection=None,evaluation_manifest=None,verifications=None):
    run=Path(run).resolve();destination=Path(destination).resolve()
    inspection=Path(inspection).resolve() if inspection else run/'inspection'
    metadata=json.loads((inspection/'vt-provenance.json').read_text())
    image=inspection/Path(metadata['image']).name
    if sha256(image)!=metadata['image_sha256'] or sha256(inspection/'vt.gemini.md')!=metadata['artifact_sha256']:
        raise ValueError('Image/transcription/provenance incompatibles')
    permissions=json.loads((inspection/'ownership-overlap-permissions.json').read_text())
    if permissions['annotations_sha256']!=sha256(inspection/'annotations.json') or permissions['image_sha256']!=sha256(image):
        raise ValueError('Audit de boîtes périmé')
    xml=(inspection/'page.alto.xml').read_bytes()
    validation=alto.validate(xml,permitted_word_overlaps=permissions['pairs'])
    files=dict(image=image,alto=inspection/'page.alto.xml',markdown=inspection/'vt.gemini.md',
               export_report=inspection/'page-export.json',ownership_audit=inspection/'ownership-audit.json',
               provenance=inspection/'vt-provenance.json',layout_preview=run/'layout/plan-preview.jpg')
    cer=inspection/'cer-hipe.json'
    if not cer.exists():cer=run/'inspection/cer-hipe.json'
    for key,path in [('cer_hipe',cer),
                     ('cer_regions',run/'transcription/cer-regions-diagnostic.json'),
                     ('box_diagnostic',inspection/'independent-box-diagnostic.json'),
                     ('boundary_recovery',inspection/'boundary-recovery-provenance.json')]:
        if path.exists():files[key]=path
    destination.mkdir(parents=True,exist_ok=True)
    copied={}
    for key,source in files.items():
        target=destination/source.name
        if source!=target:shutil.copy2(source,target)
        if sha256(source)!=sha256(target):raise ValueError('Copie altérée')
        copied[key]=str(target)
    regions=json.loads((run/'transcription/regions.json').read_text())
    if regions['image_sha256']!=metadata['image_sha256']:raise ValueError('Régions issues d’une autre image')
    native=[]
    for region in regions['regions']:
        provenance=run/'transcription'/region['id']/'vt-provenance.json'
        item=json.loads(provenance.read_text())
        if item['image_sha256']!=region['image_sha256'] or sha256(region['image'])!=region['image_sha256']:
            raise ValueError('Image région modifiée')
        native.append(dict(id=region['id'],coverage=coverage(region,item),
                           reading_status=item.get('reading_status'),uncertain=item['uncertain']))
    audit=destination/'native-audit.json';save_json(audit,native);copied['native_audit']=str(audit)
    report=json.loads(files['export_report'].read_text())
    manifest=dict(files=copied,sha256={k:sha256(p) for k,p in copied.items()},
                  source_run=str(run),source_inspection=str(inspection),
                  words=len(etree.fromstring(xml).findall('.//{%s}String'%alto.NS)),
                  text_coverage=report['text_coverage'],alto_validation=validation,
                  reading_certified=False,geometry_certified=False,
                  interrupted_regions=metadata.get('interrupted_regions',[]),empty_regions=metadata.get('empty_regions',[]))
    manifest['incomplete_pixel_coverage_regions']=[r['id'] for r in native if r['coverage']['fraction']!=1]
    if 'cer_hipe' in files:
        manifest['cer_hipe_reference_xml_order']=json.loads(files['cer_hipe'].read_text())['text']['hipe_ocrepair_2026']
    if 'cer_regions' in files:
        regional=json.loads(files['cer_regions'].read_text())
        manifest['cer_hipe_common_spatial_order']=regional.get('whole_page_same_spatial_reference_order',{}).get('regions')
        manifest['regions_without_reference_text']=regional['regions_without_reference_text']
        manifest['conditional_regions_with_reference']=regional['conditional_regions_with_reference']
    if evaluation_manifest:
        # Rapport complet des écarts Gemini ↔ VT : évaluation a posteriori seulement.
        from rapport_differences import build
        differences=build(evaluation_manifest,run/'transcription',inspection,destination,
                          title=f"{Path(metadata['image']).stem}",verifications=verifications)
        manifest['differences_gemini_vt']=dict(report=str(destination/'differences.html'),
            data=str(destination/'differences.json'),total=differences['differences'],
            by_category=differences['by_category'],visually_verified=differences['visually_verified'])
    save_json(destination/'livraison.json',manifest)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('destination');p.add_argument('--inspection')
    p.add_argument('--evaluation-manifest',help='Produit aussi le rapport complet des écarts Gemini–VT')
    p.add_argument('--verifications',help='Vérifications visuelles tracées (JSON)')
    a=p.parse_args();r=deliver(a.run,a.destination,a.inspection,a.evaluation_manifest,a.verifications)
    print(json.dumps(dict(destination=a.destination,words=r['words'],text_coverage=r['text_coverage'])))
