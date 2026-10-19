#!/usr/bin/env python
"""Image entière → VT Gemini Markdown persistante, sans références."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from page_markdown import PageMarkdownReader
from page_native_markdown import NativeMarkdownReader
from page_paged_markdown import PagedMarkdownReader
from page_minimal_markdown import MinimalMarkdownReader


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('output')
    ap.add_argument('--gemini-pane', required=True)
    ap.add_argument('--timeout', type=int, default=900)
    ap.add_argument('--native-markdown',action='store_true')
    ap.add_argument('--paged-markdown',action='store_true')
    ap.add_argument('--minimal-markdown',action='store_true')
    ap.add_argument('--tile-size',type=int,default=1536)
    args = ap.parse_args()
    output = Path(args.output)
    if sum([args.paged_markdown,args.native_markdown,args.minimal_markdown])>1:ap.error('Choisir un seul protocole Markdown')
    reader = (MinimalMarkdownReader(args.gemini_pane,output/'page-lecture-jobs',args.timeout) if args.minimal_markdown else
              PagedMarkdownReader(args.gemini_pane,output/'page-lecture-jobs',args.timeout) if args.paged_markdown else
              NativeMarkdownReader(args.gemini_pane, output/'page-lecture-jobs', args.timeout,args.tile_size)
              if args.native_markdown else PageMarkdownReader(args.gemini_pane, output/'page-lecture-jobs', args.timeout))
    reading = reader.read_page(args.image, output)
    print(json.dumps(dict(artifact=str(output/'vt.gemini.md'), characters=len(reading.text),
                         uncertain=reading.uncertain, job_id=reading.job_id), ensure_ascii=False))
