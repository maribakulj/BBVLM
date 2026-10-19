#!/usr/bin/env python
"""Requalifier un incident natif ancien sans en faire un refus de lecture.

Les preuves originales sont conservées ; seuls les placements intermédiaires
touchés par un quota explicite sont déplacés vers une quarantaine réversible.
Aucune sortie achevée ni transcription validée n'est modifiée.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from native_quota import quota_observation,observe,save


def repair(directory,pane):
    directory=Path(directory)
    if (directory/'annotations.json').exists() or (directory/'provenance.json').exists():
        raise ValueError('Sortie achevée : utiliser un nouvel essai pour conserver le verdict historique')
    audit_file=directory/'quota-cache-repair.json'
    if audit_file.exists():return json.loads(audit_file.read_text())
    affected=[]
    for job in (directory/'lecture-jobs').iterdir():
        if not (job/'request.json').exists() or not (job/'terminal.txt').exists() or (job/'response.json').exists():continue
        manifest=json.loads((job/'request.json').read_text())
        terminal=job/'terminal.txt';observed_at=terminal.stat().st_mtime
        evidence=quota_observation(terminal.read_text(),manifest['job_id'],observed_at)
        if evidence is None:continue
        evidence=observe(pane,job,terminal.read_text(),manifest['job_id'],observed_at)
        affected.append(dict(directory=str(job.resolve()),ids=[r['id'] for r in manifest['lines']],evidence=evidence))
    ids={lid for job in affected for lid in job['ids']};moved=[]
    quarantine=directory/'quota-quarantine/geometry-cache'
    for path in (directory/'geometry-cache').glob('*.json'):
        if path.name=='state.json':continue
        value=json.loads(path.read_text())
        if value['annotation']['id'] not in ids:continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        target=quarantine/path.name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():raise ValueError('Quarantaine déjà occupée : '+str(target))
        path.rename(target)
        moved.append(dict(id=value['annotation']['id'],source=str(path.resolve()),
                          quarantine=str(target.resolve()),sha256=digest,previous_status=value['annotation']['status']))
    report=dict(affected_jobs=affected,affected_line_ids=sorted(ids),quarantined_placements=moved,
                created_at=time.time(),pane=pane,criteria_met=False,
                scope='explicit native service quota; validated initial readings and original evidence preserved; no content refusal inferred')
    save(audit_file,report);return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory');ap.add_argument('--gemini-pane',required=True)
    args=ap.parse_args();report=repair(args.directory,args.gemini_pane)
    print(json.dumps(dict(affected_jobs=len(report['affected_jobs']),affected_lines=len(report['affected_line_ids']),
                         quarantined_placements=len(report['quarantined_placements']),criteria_met=False)))
