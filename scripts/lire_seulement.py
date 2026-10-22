#!/usr/bin/env python
"""Lecture seule d'une page (sans géométrie) sur un plan de régions existant : image plan.json sortie lecteur."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from transcrire_regions import prepare, transcribe

image, plan, output, pane = sys.argv[1:5]
manifest = prepare(image, json.loads(Path(plan).read_text()), Path(output))
transcribe(manifest, Path(output), pane)
