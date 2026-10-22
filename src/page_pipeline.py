"""VT de page immuable → ancres → appariement → géométrie → exports.

Ce module ne lance pas Gemini : il consomme une transcription déjà sauvegardée
avec sa provenance. Un worker Kraken séparé évite de mélanger les environnements.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image
from page_anchors import cached_reading_anchors, load_automatic_lines, save_json, sha256


ROOT = Path(__file__).resolve().parents[1]
KRAKEN_PYTHON = Path.home() / 'outils-seg/kraken-env/bin/python'
VERSION = 'page-markdown-pipeline-v2'


def implementation_fingerprints():
    """Ne pas mélanger plusieurs algorithmes lors d'une reprise de page."""
    files = ('page_pipeline.py', 'page_anchors.py', 'page_alignment.py', 'page_text_view.py',
             'page_olr.py', 'page_geometry.py', 'page_export.py', 'page_character_audit.py',
             'placement_cache.py', 'boxers/forcectc.py', 'ink.py', 'correct.py',
             'alto.py', 'export_training.py', 'page_geometry_repair.py', 'page_word_ownership.py',
             'page_line_split.py', 'block_ctc.py', 'page_orphan_lines.py')
    return {name: sha256(ROOT / 'src' / name) for name in files}


def _assert_implementation(config):
    if config.get('implementation_sha256') != implementation_fingerprints():
        raise ValueError('Implémentation modifiée pendant la page ; employer un nouveau dossier')


def verify_transcription(image, markdown, provenance):
    image, markdown, provenance = Path(image), Path(markdown), Path(provenance)
    data = json.loads(provenance.read_text())
    if data.get('image_sha256') != sha256(image) or data.get('artifact_sha256') != sha256(markdown):
        raise ValueError('Transcription, image et provenance ne correspondent pas')
    if data.get('provider') not in ('gemini', 'anthropic') or not data.get('job_id'):
        raise ValueError('Transcription sans provenance de lecteur (Gemini ou Claude)')
    return data


def prepare_lines(image, automatic_lines, region_plan=None, block_ctc=False):
    """Lignes que liront le CTC et l'appariement : lignes automatiques, coupées aux
    gouttières observées, plus les lignes d'encre orpheline. Ne dépend que de
    l'image et du plan (pas de la transcription) : peut tourner pendant la
    lecture Gemini (scripts/prechauffer_ctc.py)."""
    image, automatic_lines = Path(image).resolve(), Path(automatic_lines).resolve()
    lines = load_automatic_lines(image, automatic_lines)
    # Option : contrainte régionale issue du plan automatique figé. Elle ne lit
    # que les sorties source (plan de régions, offsets de la transcription).
    constraint = None
    if region_plan is not None:
        plan_data = json.loads(Path(region_plan).read_text())
        if plan_data.get('image_sha256') != sha256(image):
            raise ValueError('Le plan de régions appartient à une autre image')
        constraint = dict(plan=str(Path(region_plan).resolve()), plan_sha256=sha256(region_plan),
                          line_regions=plan_data['line_regions'])
        # Les lignes BLLA qui traversent une gouttière observée sont coupées
        # avant toute lecture CTC ; chaque morceau reçoit la région de son centre.
        import numpy as np
        from page_line_split import split_crossing_lines, assign_regions, VERSION as SPLIT_VERSION
        with Image.open(image) as page:
            gray = np.asarray(page.convert('L'))
        lines, split_log = split_crossing_lines(gray, lines, plan_data)
        split_regions = assign_regions([l for l in lines if 'split_from' in l], plan_data)
        constraint['line_regions'] = {**{k: v for k, v in constraint['line_regions'].items()
                                         if not any(e.get('decision') == 'split_at_observed_gutter'
                                                    and e['id'] == k for e in split_log)},
                                      **split_regions}
        constraint.update(line_split=dict(version=SPLIT_VERSION, log=split_log))
        if block_ctc:
            # Encre qu'aucune ligne détectée ne couvre (colonnes de chiffres des
            # tableaux, fins de paragraphe) : nouvelles lignes, texte par CTC.
            from page_orphan_lines import find_orphan_lines, VERSION as ORPHAN_VERSION
            orphans = find_orphan_lines(gray, lines, plan_data['parameters']['line_height'],
                                        regions=[r['bbox'] for r in plan_data['regions']])
            constraint['line_regions'].update(assign_regions(orphans, plan_data))
            lines = lines + orphans
            constraint['orphan_lines'] = dict(version=ORPHAN_VERSION, ids=[o['id'] for o in orphans])
    return lines, constraint


def run(image, markdown, provenance, automatic_lines, output, *, anchor_reader='cached',
        geometry=True, kraken_python=KRAKEN_PYTHON, model_path=None,
        minimum_similarity=.72, ambiguity_margin=.06, repair_ownership=False, region_plan=None,
        block_ctc=False):
    from page_alignment import write_alignment
    from page_olr import write_structure
    image, markdown = Path(image).resolve(), Path(markdown).resolve()
    automatic_lines, output = Path(automatic_lines).resolve(), Path(output).resolve()
    if not geometry and any((output / name).exists() for name in ('annotations.json', 'page.alto.xml', 'training.jsonl')):
        raise ValueError('Des placements existent déjà ; choisir un nouveau dossier pour l’appariement seul')
    metadata = verify_transcription(image, markdown, provenance)
    lines, constraint = prepare_lines(image, automatic_lines, region_plan, block_ctc)
    if constraint is not None:
        constraint['region_spans'] = {p['id']: p['span'] for p in metadata.get('parts', [])}
        if not constraint['region_spans']:
            raise ValueError('Transcription sans offsets de régions')
    config = dict(version=VERSION, image_sha256=sha256(image), markdown_sha256=sha256(markdown),
                  provenance_sha256=sha256(provenance),
                  provenance_source=str(Path(provenance).resolve()),
                  segmentation_sha256=sha256(automatic_lines / 'segmentation.json'),
                  segmentation_config_sha256=sha256(automatic_lines / 'segmentation-config.json'),
                  implementation_sha256=implementation_fingerprints(),
                  anchor_reader=anchor_reader, repair_ownership=repair_ownership, minimum_similarity=minimum_similarity,
                  ambiguity_margin=ambiguity_margin, model_path=str(model_path) if model_path else None,
                  block_ctc=block_ctc)
    if constraint is not None:
        config['region_constraint_plan_sha256'] = constraint['plan_sha256']
    if anchor_reader == 'cached':
        config['readings_sha256'] = sha256(automatic_lines / 'readings.json')
    elif anchor_reader != 'ctc':
        raise ValueError('Lecteur d’ancres inconnu')
    output.mkdir(parents=True, exist_ok=True)
    config_path = output / 'page-pipeline-config.json'
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError('Configuration de page modifiée ; employer un nouveau dossier')
    save_json(config_path, config)
    # Une copie byte-identique de toute la VT précède toute localisation.
    target = output / 'vt.gemini.md'
    if target.exists() and sha256(target) != config['markdown_sha256']:
        raise ValueError('La VT de sortie existe avec un autre contenu')
    if target.resolve() != markdown:
        target.write_bytes(markdown.read_bytes())
    if Path(provenance).resolve() != (output / 'vt-provenance.json').resolve():
        save_json(output / 'vt-provenance.json', {**metadata, 'source_artifact': str(markdown)})
    save_json(output / 'segmentation.json', lines)
    if constraint is not None:
        save_json(output / 'region-constraint.json', constraint)

    def checkpoint(stage, **kwargs):
        save_json(output / 'page-pipeline-state.json', dict(stage=stage, criteria_met=False, **kwargs))

    def assert_frozen_inputs():
        _assert_implementation(config)
        paths = [(image, 'image_sha256'), (markdown, 'markdown_sha256'),
                 (target, 'markdown_sha256'), (Path(provenance), 'provenance_sha256'),
                 (automatic_lines / 'segmentation.json', 'segmentation_sha256'),
                 (automatic_lines / 'segmentation-config.json', 'segmentation_config_sha256')]
        if anchor_reader == 'cached':
            paths.append((automatic_lines / 'readings.json', 'readings_sha256'))
        if any(sha256(path) != config[key] for path, key in paths):
            raise ValueError('Entrée modifiée pendant la page ; employer un nouveau dossier')

    def worker(kind):
        assert_frozen_inputs()
        command = [str(kraken_python), str(Path(__file__)), '--worker', kind,
                   '--image', str(image), '--output', str(output)]
        if model_path:
            command.extend(['--model', str(model_path)])
        with (output / (kind + '.log')).open('a', encoding='utf-8') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        assert_frozen_inputs()

    try:
        checkpoint('automatic_anchors')
        if anchor_reader == 'cached':
            anchors = cached_reading_anchors(image, automatic_lines)
            save_json(output / 'anchors.json', anchors)
        else:
            worker('anchors')
            anchors = json.loads((output / 'ctc-anchors/anchors.json').read_text())
            save_json(output / 'anchors.json', anchors)
        checkpoint('text_alignment')
        with Image.open(image) as page:
            size = page.size
        regional = {} if constraint is None else dict(line_regions=constraint['line_regions'],
                                                       region_spans=constraint['region_spans'])
        if block_ctc and constraint is not None:
            # Probabilités CTC de chaque ligne (même modèle que les ancres) pour
            # découper le texte Gemini entre lignes par vraisemblance (block_ctc).
            checkpoint('ctc_posteriors')
            anchor_model = json.loads((output / 'ctc-anchors/anchors-config.json').read_text())['model']['path'] \
                if (output / 'ctc-anchors/anchors-config.json').exists() else model_path
            posterior_dir = output / 'ctc-posteriors'
            if not (posterior_dir / 'posteriors.npz').exists():
                assert_frozen_inputs()
                with (output / 'ctc-posteriors.log').open('a', encoding='utf-8') as log:
                    subprocess.run([str(kraken_python), str(ROOT / 'scripts/ctc_posteriors.py'), str(image),
                                    str(output / 'segmentation.json'), str(posterior_dir), '--model', str(anchor_model)],
                                   stdout=log, stderr=subprocess.STDOUT, check=True)
            from block_ctc import Posteriors
            regional['ctc_posteriors'] = Posteriors(posterior_dir)
        alignment = write_alignment(target, anchors['lines'], output, image_size=size,
                                    minimum_similarity=minimum_similarity, ambiguity_margin=ambiguity_margin,
                                    **regional)
        write_structure(alignment, output)
        if not geometry:
            assert_frozen_inputs()
            checkpoint('alignment_ready', text_coverage=alignment['text_coverage'])
            return alignment
        checkpoint('word_geometry', text_coverage=alignment['text_coverage'])
        worker('geometry')
        annotations = json.loads((output / 'annotations.json').read_text())
        if repair_ownership:
            checkpoint('pixel_ownership')
            from page_geometry_repair import repair
            alignment, annotations = repair(image, output)
        write_structure(alignment, output, annotations)
        checkpoint('structured_exports')
        from page_export import export
        assert_frozen_inputs()
        report = export(image, output)
        assert_frozen_inputs()
        checkpoint('exported_pending_independent_evaluation', report=report)
        return report
    except Exception as exc:
        checkpoint('interrupted', error=f'{type(exc).__name__}: {exc}',
                   original_markdown_preserved=sha256(target) == config['markdown_sha256'])
        raise


def _worker(kind, image, output, model_path=None):
    output = Path(output)
    config = json.loads((output / 'page-pipeline-config.json').read_text())
    _assert_implementation(config)
    if sha256(config['provenance_source']) != config['provenance_sha256']:
        raise ValueError('Provenance modifiée avant le worker')
    verify_transcription(image, output / 'vt.gemini.md', output / 'vt-provenance.json')
    if kind == 'anchors':
        from page_anchors import ctc_anchors
        ctc_anchors(image, json.loads((output / 'segmentation.json').read_text()),
                    output / 'ctc-anchors', model_path=model_path)
        return
    from page_geometry import place_assignments
    from boxers.forcectc import ForceCTC
    alignment = json.loads((output / 'page-alignment.json').read_text())
    metadata = json.loads((output / 'vt-provenance.json').read_text())
    metadata['model'] = metadata.get('model_claim', metadata.get('model', 'unknown'))
    metadata['page_reading_uncertain'] = metadata.get('uncertain')
    automatic = {line['id']: line for line in json.loads((output / 'segmentation.json').read_text())}
    assignments = [{**row, 'detector_bbox': automatic[row['line_id']].get('detector_bbox', row['bbox'])}
                   for row in alignment['assignments']]
    assignments.extend({**row, 'text': '', 'assignment_resolved': False}
                       for row in alignment['unmatched_lines'])
    place_assignments(image, assignments,
                      boxer=ForceCTC(model_path, boundary_mode='ink_clean_local', char_alignment='word'),
                      output_dir=output, metadata=metadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', choices=('anchors', 'geometry'), required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model')
    args = parser.parse_args()
    _worker(args.worker, args.image, args.output, args.model)
