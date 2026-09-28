#!/usr/bin/env python3
"""Durable local DAG dispatcher. External work requires a real active orchestrator.

No model API, fabricated inference, automatic scientific gate, or git publication.
An interrupted command requires explicit retry with a new job ID/output path.
"""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class Queue:
    def __init__(self, root, manifest, state):
        self.root = Path(root).resolve()
        self.state_path = Path(state)
        self.spec = json.loads(Path(manifest).read_text())
        self.jobs = {j['id']: j for j in self.spec['jobs']}
        if len(self.jobs) != len(self.spec['jobs']):
            raise ValueError('duplicate job IDs')
        self.limits = self.spec.get('resources', {'cpu': 1, 'io': 2, 'vlm': 1, 'orchestrator': 1})
        if any(not isinstance(n, int) or n < 1 for n in self.limits.values()):
            raise ValueError('resource limits must be positive integers')
        outputs = set()
        for key, job in self.jobs.items():
            if not re.fullmatch(r'[A-Za-z0-9_-]+', key):
                raise ValueError('unsafe job ID')
            if job['kind'] not in ('command', 'external') or job['resource'] not in self.limits:
                raise ValueError('unknown kind/resource')
            if key in job.get('deps', []) or set(job.get('deps', [])) - self.jobs.keys():
                raise ValueError('invalid dependencies')
            if not job.get('outputs'):
                raise ValueError('completion requires at least one evidence artifact')
            for path in job.get('inputs', []) + job['outputs']:
                self.path(path)
            if outputs.intersection(job['outputs']):
                raise ValueError('jobs must not share output paths')
            outputs.update(job['outputs'])
            if job['kind'] == 'command':
                if not job.get('argv') or not all(isinstance(x, str) for x in job['argv']):
                    raise ValueError('argv must be a nonempty string array; no shell')
                if job.get('timeout_seconds', 0) <= 0:
                    raise ValueError('positive timeout required')
        visited, visiting = set(), set()
        def visit(key):
            if key in visiting:
                raise ValueError('dependency cycle')
            if key not in visited:
                visiting.add(key)
                for dep in self.jobs[key].get('deps', []):
                    visit(dep)
                visiting.remove(key)
                visited.add(key)
        for key in self.jobs:
            visit(key)
        self.order = []
        def order(key):
            for dep in self.jobs[key].get('deps', []):
                order(dep)
            if key not in self.order:
                self.order.append(key)
        for key in self.jobs:
            order(key)
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {'jobs': {}}
        self.running = {}

    def path(self, name):
        p = (self.root / name).resolve()
        if Path(name).is_absolute() or not p.is_relative_to(self.root):
            raise ValueError('artifact paths must stay inside the project')
        return p

    def save(self):
        atomic_json(self.state_path, self.state)

    @contextmanager
    def lock(self):
        # Same lock as the legacy runner and checkpoint aggregation.
        path = self.root / 'experiments/loop/runner.lock'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Reload after lock: two Queue objects may have been created together.
            if self.state_path.exists():
                self.state = json.loads(self.state_path.read_text())
            yield

    def fingerprint(self, job):
        data = {'job': job, 'inputs': {p: digest(self.path(p)) for p in job.get('inputs', [])},
                'dependencies': {p: self.state['jobs'][p].get('outputs') for p in job.get('deps', [])}}
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def reconcile(self):
        rows = self.state['jobs']
        for key in self.order:
            job = self.jobs[key]
            row = rows.setdefault(key, {'status': 'pending'})
            if row['status'] == 'running':
                # A previous coordinator lost control; never launch a duplicate.
                row.update(status='interrupted', reason='Inspect recorded PID/process group and outputs before an explicit new attempt.')
            if row['status'] in ('completed', 'claimed'):
                try:
                    valid = row['fingerprint'] == self.fingerprint(job)
                    valid &= all(rows[d]['status'] == 'completed' for d in job.get('deps', []))
                    if row['status'] == 'completed':
                        valid &= row['outputs'] == self.output_hashes(job)
                except (OSError, ValueError, KeyError):
                    valid = False
                if not valid:
                    row.update(status='stale', reason='Inputs, dependencies, job definition or output evidence changed; no automatic rerun.')
        self.save()

    def output_hashes(self, job):
        result = {}
        for p in job['outputs']:
            if p.endswith('.json'):
                json.loads(self.path(p).read_text())
            result[p] = digest(self.path(p))
        return result

    def ready(self, key):
        job = self.jobs[key]
        return (self.state['jobs'][key]['status'] == 'pending'
                and all(self.state['jobs'][d]['status'] == 'completed' for d in job.get('deps', []))
                and all(self.path(p).is_file() for p in job.get('inputs', [])))

    def capacity(self, resource):
        used = sum((r['status'] in ('running', 'claimed', 'interrupted')
                    or (r['status'] == 'stale' and 'token' in r)) and
                   self.jobs.get(k, {}).get('resource') == resource for k, r in self.state['jobs'].items())
        return used < self.limits[resource]

    def start_row(self, key, status):
        job = self.jobs[key]
        if any(self.path(p).exists() for p in job['outputs']):
            self.state['jobs'][key].update(status='blocked', reason='Output already exists without matching completion receipt; preserve it and investigate.')
            self.save()
            return None
        row = self.state['jobs'][key]
        row.update(status=status, started_at=time.time(), fingerprint=self.fingerprint(job))
        self.save()
        return row

    def finish(self, key, success, reason=None):
        row = self.state['jobs'][key]
        try:
            if not success:
                raise ValueError(reason or 'command failed')
            if self.fingerprint(self.jobs[key]) != row['fingerprint']:
                raise ValueError('inputs changed while task was active')
            row.update(outputs=self.output_hashes(self.jobs[key]), status='completed')
        except (ValueError, OSError) as exc:
            row.update(status='failed', reason=str(exc))
        row['ended_at'] = time.time()
        self.save()

    def claim(self, key, actor):
        self.reconcile()
        job = self.jobs[key]
        if job['kind'] != 'external' or not self.ready(key) or not self.capacity(job['resource']):
            raise ValueError('external task unavailable or resource occupied')
        row = self.start_row(key, 'claimed')
        if row is None:
            raise ValueError('unowned existing output')
        row.update(actor=actor, token=uuid.uuid4().hex)
        self.save()
        return row

    def complete(self, key, token):
        self.reconcile()
        row = self.state['jobs'][key]
        if row['status'] != 'claimed' or row['token'] != token:
            raise ValueError('claim mismatch; external results cannot be invented or adopted implicitly')
        self.finish(key, True)
        return row

    @staticmethod
    def stop(process):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()

    def run(self, seconds=2700):
        if seconds <= 0:
            raise ValueError('run budget must be positive')
        self.reconcile()
        deadline = time.monotonic() + seconds
        try:
            while True:
                for key in self.order:
                    job = self.jobs[key]
                    if (time.monotonic() >= deadline or job['kind'] != 'command'
                            or not self.ready(key) or not self.capacity(job['resource'])):
                        continue
                    row = self.start_row(key, 'running')
                    if row is None:
                        continue
                    log_path = self.state_path.parent / 'logs' / (key + '.log')
                    log_path.parent.mkdir(exist_ok=True)
                    log = log_path.open('ab')
                    env = dict(os.environ, OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4',
                               PYTHONPATH=str(self.root / 'src'))
                    argv = [sys.executable if x == '{python}' else x for x in job['argv']]
                    try:
                        proc = subprocess.Popen(argv, cwd=self.root, env=env, stdout=log,
                                                stderr=subprocess.STDOUT, start_new_session=True)
                    except OSError as exc:
                        log.close()
                        self.finish(key, False, str(exc))
                        continue
                    row.update(pid=proc.pid, log=str(log_path.relative_to(self.root)))
                    self.running[key] = (proc, log, min(deadline, time.monotonic() + job['timeout_seconds']))
                    self.save()
                for key, (proc, log, expires) in list(self.running.items()):
                    timed_out = proc.poll() is None and time.monotonic() >= expires
                    if timed_out:
                        self.stop(proc)
                    if proc.poll() is not None:
                        log.close()
                        self.state['jobs'][key]['returncode'] = proc.returncode
                        self.finish(key, not timed_out and proc.returncode == 0,
                                    'timeout/run deadline' if timed_out else 'command exited nonzero')
                        del self.running[key]
                if not self.running:
                    can_start = any(self.jobs[k]['kind'] == 'command' and self.ready(k)
                                    and self.capacity(self.jobs[k]['resource']) for k in self.order)
                    if not can_start or time.monotonic() >= deadline:
                        break
                # Poll only while a real child process is active, never wait for an agent.
                if self.running:
                    time.sleep(.05)
        finally:
            for key, (proc, log, _) in list(self.running.items()):
                self.stop(proc)
                log.close()
                self.finish(key, False, 'coordinator interrupted')
            self.running.clear()
        return self.summary()

    def summary(self):
        return {'jobs': {k: v['status'] for k, v in self.state['jobs'].items()},
                'ready_external': [{'id': k, 'instructions': j.get('instructions', ''),
                                    'resource': j['resource'], 'can_claim': self.capacity(j['resource'])}
                                   for k, j in self.jobs.items() if j['kind'] == 'external' and self.ready(k)],
                'waiting': {k: {'dependencies': [d for d in j.get('deps', []) if self.state['jobs'][d]['status'] != 'completed'],
                                'missing_inputs': [p for p in j.get('inputs', []) if not self.path(p).is_file()]}
                            for k, j in self.jobs.items() if self.state['jobs'][k]['status'] == 'pending' and not self.ready(k)},
                'scientific_success': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', default='experiments/loop/queue.json')
    p.add_argument('--state', default='experiments/loop/queue-state.json')
    p.add_argument('--budget-seconds', type=float, default=2700)
    action = p.add_mutually_exclusive_group()
    action.add_argument('--execute', action='store_true')
    action.add_argument('--claim')
    action.add_argument('--complete')
    p.add_argument('--actor')
    p.add_argument('--token')
    a = p.parse_args()
    q = Queue(ROOT, ROOT / a.manifest, ROOT / a.state)
    try:
        with q.lock():
            if a.execute:
                result = q.run(a.budget_seconds)
            elif a.claim:
                if not a.actor:
                    p.error('--claim requires --actor')
                result = q.claim(a.claim, a.actor)
            elif a.complete:
                result = q.complete(a.complete, a.token)
            else:
                q.reconcile()
                result = q.summary()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except BlockingIOError:
        raise SystemExit('An existing runner owns the lock. Do independent read-only research; do not duplicate work.')


if __name__ == '__main__':
    main()
