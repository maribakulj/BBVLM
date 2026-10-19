#!/usr/bin/env python
"""Relit avec un autre modèle les planches déjà lues par Argon (comparaison de modèles).

Écrit ``lecture-<suffixe>.jsonl`` à côté de ``lecture.jsonl`` ; reprise possible.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from line_reader import ask, LINE_PROMPT

parser = argparse.ArgumentParser()
parser.add_argument('passes', nargs='+')
parser.add_argument('--source-model', default='gemini-4-argon-medium')
parser.add_argument('--model', default='gemini-3.8-flash-medium')
parser.add_argument('--suffix', default='flash')
parser.add_argument('--workers', type=int, default=2)
args = parser.parse_args()
jobs = []
for directory in map(Path, args.passes):
    source = [json.loads(r) for r in (directory / 'lecture.jsonl').read_text().splitlines()]
    out = directory / f'lecture-{args.suffix}.jsonl'
    done = {json.loads(r)['sheet'] for r in out.read_text().splitlines()} if out.exists() else set()
    jobs += [(directory, r['sheet']) for r in source if r['model'] == args.source_model and r['sheet'] not in done]
print(len(jobs), 'planches à relire', flush=True)


def one(job):
    directory, sheet = job
    log = []
    answer = ask(directory, sheet, LINE_PROMPT, model=args.model, timeout=720, log=log)
    return directory, dict(sheet=sheet, model=args.model, answer=answer, log=log)


with ThreadPoolExecutor(args.workers) as pool:
    for directory, row in pool.map(one, jobs):
        with (directory / f'lecture-{args.suffix}.jsonl').open('a') as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
        print(directory.name, row['sheet'], 'ok' if row['answer'] is not None else 'FAILED', flush=True)
