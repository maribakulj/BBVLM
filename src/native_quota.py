"""Observation persistante d'un quota natif, jamais déduite d'un timeout."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import time

SERVICE_DIRECTORY=Path(__file__).resolve().parents[1]/'runs/gemini-service-state'


def quota_observation(terminal,job_id,observed_at=None):
    position=terminal.rfind('Individual quota reached.')
    start=terminal.rfind(job_id,0,position)
    if position<0 or start<0:return None
    ids=re.findall(r'(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])',terminal[start:position])
    if any(value!=job_id for value in ids):return None
    tail=terminal[position:]
    match=re.search(r'Resets in\s+(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?\.',tail)
    error=re.search(r'Error ID:\s*([\w-]+)',tail)
    if not match or not any(match.groups()) or not error:return None
    seconds=sum(int(value or 0)*unit for value,unit in zip(match.groups(),(3600,60,1)))
    observed_at=time.time() if observed_at is None else observed_at
    return dict(job_id=job_id,error_id=error[1],observed_at=observed_at,
                reset_seconds=seconds,retry_at=observed_at+seconds+30,
                terminal_sha256=hashlib.sha256(terminal.encode()).hexdigest(),
                basis='explicit native individual-quota error and displayed reset duration',
                blind_timeout_retry=False)


def service_path(pane):
    return SERVICE_DIRECTORY/(hashlib.sha256(pane.encode()).hexdigest()+'.json')


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2));temporary.replace(path)


def observe(pane,directory,terminal,job_id,observed_at=None):
    observation=quota_observation(terminal,job_id,observed_at)
    if observation is None:return None
    marker=Path(directory)/'quota-interruption.json'
    previous=json.loads(marker.read_text()) if marker.exists() else None
    if previous and previous['error_id']==observation['error_id']:
        observation=previous
    observation={**observation,'pane':pane}
    save(marker,observation)
    shared=service_path(pane)
    current=json.loads(shared.read_text()) if shared.exists() else None
    if current and current['error_id']==observation['error_id']:observation=current
    elif current is None or observation['retry_at']>=current['retry_at']:
        save(shared,observation)
    return observation


def pending(pane,now=None):
    path=service_path(pane)
    if not path.exists():return None
    value=json.loads(path.read_text())
    if value['pane']!=pane:raise ValueError('Quota partagé d’un autre terminal')
    return value if (time.time() if now is None else now)<value['retry_at'] else None
