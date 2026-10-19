"""Finaliser une reprise CTC sans remplacer les résultats initiaux."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from page_anchors import save_json,sha256

ROOT=Path(__file__).resolve().parents[1]


def finalize(image,source,recovery,output,contrast='otsu'):
    from page_alignment import write_alignment
    from page_geometry_repair import repair
    from page_olr import write_structure
    from page_export import export
    from PIL import Image
    source=Path(source);recovery=Path(recovery);output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    for name in ('vt.gemini.md','vt-provenance.json','provenance.json','geometry-report.json'):
        shutil.copy2(source/name,output/name)
    rows=json.loads((recovery/'annotations.json').read_text())
    save_json(output/'annotations.json',rows)
    anchors=json.loads((source/'anchors.json').read_text())
    with Image.open(image) as page:size=page.size
    original=json.loads((source/'page-pipeline-config.json').read_text())
    regional={}
    if (source/'region-constraint.json').exists():
        constraint=json.loads((source/'region-constraint.json').read_text())
        if sha256(constraint['plan'])!=original.get('region_constraint_plan_sha256'):
            raise ValueError('Plan de régions modifié depuis la page initiale')
        shutil.copy2(source/'region-constraint.json',output/'region-constraint.json')
        regional=dict(line_regions=constraint['line_regions'],region_spans=constraint['region_spans'])
    if original.get('block_ctc') and (source/'ctc-posteriors'/'posteriors.npz').exists():
        # Même appariement que la page initiale : sans les probabilités CTC, le
        # découpage des cellules diffère et ne correspond plus à la géométrie.
        from block_ctc import Posteriors
        regional['ctc_posteriors']=Posteriors(source/'ctc-posteriors')
    write_alignment(output/'vt.gemini.md',anchors['lines'],output,image_size=size,
                    minimum_similarity=original['minimum_similarity'],ambiguity_margin=original['ambiguity_margin'],
                    **regional)
    alignment,rows=repair(image,output,contrast=contrast)
    write_structure(alignment,output,rows)
    report=export(image,output)
    geometry=json.loads((output/'geometry-report.json').read_text())
    geometry.update(coverage=report['coverage'],lines_preserved=len(rows),
                    lines_placed=sum(bool(r.get('words')) for r in rows),
                    alto_validation=report['alto_validation'])
    save_json(output/'geometry-report.json',geometry)
    save_json(output/'boundary-recovery-provenance.json',dict(
        source=str(source.resolve()),source_config_sha256=sha256(source/'page-pipeline-config.json'),
        recovery=str(recovery.resolve()),recovery_annotations_sha256=sha256(recovery/'annotations.json'),
        recovery_report=json.loads((recovery/'report.json').read_text()),text_changed=False,
        contrast=contrast,implementation_sha256={name:sha256(ROOT/'src'/name) for name in
          ('page_boundary_recovery.py','page_geometry_repair.py','page_word_ownership.py','page_export.py','alto.py')}))
    return report


def recover(image,source,output,kraken_python):
    source=Path(source);output=Path(output)
    recovery=output.parent/(output.name+'-work')
    subprocess.run([str(kraken_python),str(ROOT/'scripts/reparer_frontieres.py'),
                    str(image),str(source),str(recovery)],check=True)
    return finalize(image,source,recovery,output)
