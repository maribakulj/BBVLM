"""Notation indépendante de VT Markdown ; jamais une entrée de production."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import importlib.metadata
import json
from pathlib import Path
import re

from evaluation import (nfc, convention, convention_v2, lev, load_reference,
                        hipe_ocrepair_2026, cer_vt, HIPE_NORMALIZATION_SOURCE,
                        HIPE_NORMALIZATION_SOURCE_SHA256)
from page_reference_text import load_page_reference


class _HTMLText(HTMLParser):
    """Retire le HTML de présentation, en signalant les balises inconnues."""

    inline_tags = {'a', 'abbr', 'b', 'big', 'cite', 'code', 'del', 'em', 'font',
                   'i', 'ins', 'kbd', 'mark', 'q', 's', 'samp', 'small', 'span',
                   'strike', 'strong', 'sub', 'sup', 'time', 'tt', 'u', 'var', 'wbr'}
    block_tags = {'address', 'article', 'aside', 'blockquote', 'caption', 'center',
                  'dd', 'div', 'dl', 'dt', 'figcaption', 'figure', 'footer',
                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'li', 'main',
                  'ol', 'p', 'pre', 'section', 'table', 'tbody', 'td', 'tfoot',
                  'th', 'thead', 'tr', 'ul'}

    def __init__(self, unhandled):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.unhandled = unhandled

    def handle_starttag(self, tag, attrs):
        if tag in self.block_tags or tag in {'br', 'hr'}:
            self.parts.append('\n')
        elif tag == 'img':
            self.parts.append(dict(attrs).get('alt') or '')
        elif tag not in self.inline_tags:
            self.unhandled.add(tag)
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in self.block_tags:
            self.parts.append('\n')
        elif tag not in self.inline_tags and tag not in {'br', 'hr', 'img'}:
            self.unhandled.add(tag)
            self.parts.append('</'+tag+'>')

    def handle_data(self, data):
        self.parts.append(data)


def markdown_text(markdown):
    from markdown_it import MarkdownIt
    parser = MarkdownIt('commonmark').enable('table')
    chunks = []
    unhandled = set()
    unhandled_html = set()

    def html_text(value):
        reader = _HTMLText(unhandled_html)
        reader.feed(value)
        reader.close()
        return ''.join(reader.parts)

    def inline_text(children):
        content = []
        for child in children or []:
            if child.type in {'text', 'text_special', 'code_inline'}:
                content.append(child.content)
            elif child.type == 'image':
                content.append(inline_text(child.children))
            elif child.type == 'html_inline':
                content.append(html_text(child.content))
            elif child.type in {'softbreak', 'hardbreak'}:
                content.append('\n')
            elif not child.type.endswith(('_open', '_close')):
                unhandled.add(child.type)
                content.append(child.content)
        return ''.join(content)

    for token in parser.parse(markdown):
        if token.type == 'inline':
            chunks.append(inline_text(token.children))
        elif token.type == 'html_block':
            chunks.append(html_text(token.content).strip('\n'))
        elif token.type in {'fence','code_block'}:
            chunks.append(token.content.rstrip('\n'))
        elif not token.type.endswith(('_open','_close')) and token.type != 'hr':
            unhandled.add(token.type)
            chunks.append(token.content)
    return '\n'.join(chunks), dict(parser='markdown-it-py',
            version=importlib.metadata.version('markdown-it-py'), preset='commonmark+table',
            converter='bbvlm-page-text', converter_revision=2,
            unhandled_token_types=sorted(unhandled), unhandled_html_tags=sorted(unhandled_html))


def _whitespace_only(text):
    """NFC et espaces seuls : ni apostrophe, ni césure, ni accent modifié."""
    return re.sub(r'\s+', ' ', nfc(text)).strip()


def unordered_line_diagnostic(reference_lines, text):
    """Appariement textuel optimiste, réservé à la notation et séparé de l'ordre."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from rapidfuzz import process
    from rapidfuzz.distance import Levenshtein
    prediction = [line.strip() for line in text.splitlines() if line.strip()]
    results = {}
    for name, normalizer in [('strict_NFC',nfc),('convention_v1',convention),('convention_v2',convention_v2)]:
        ref = [normalizer(line['text']) for line in reference_lines]
        hyp = [normalizer(line) for line in prediction]
        if ref and hyp:
            costs = process.cdist(ref,hyp,scorer=Levenshtein.distance,dtype=np.int32)
            gain = np.array([len(s) for s in ref])[:,None] + np.array([len(s) for s in hyp])[None,:] - costs
            rr,pp = linear_sum_assignment(gain,maximize=True)
            pairs = [(int(r),int(p),int(costs[r,p])) for r,p in zip(rr,pp)]
        else:
            pairs = []
        matched_r = {r for r,_,_ in pairs}
        matched_p = {p for _,p,_ in pairs}
        deleted = sum(len(s) for i,s in enumerate(ref) if i not in matched_r)
        inserted = sum(len(s) for i,s in enumerate(hyp) if i not in matched_p)
        errors = sum(c for _,_,c in pairs)+deleted+inserted
        denominator = sum(map(len,ref))
        sequence = [r for r,p,_ in sorted(pairs,key=lambda pair:pair[1])]
        inversions = sum(a>b for i,a in enumerate(sequence) for b in sequence[i+1:])
        total = len(sequence)*(len(sequence)-1)//2
        results[name] = dict(errors=errors,reference_characters=denominator,
            cer=errors/denominator if denominator else None,
            reference_lines=len(ref),prediction_lines=len(hyp),matched_lines=len(pairs),
            unmatched_reference_indices=[i for i in range(len(ref)) if i not in matched_r],
            unmatched_prediction_indices=[i for i in range(len(hyp)) if i not in matched_p],
            pairs=[dict(reference_id=reference_lines[r]['id'] if 'id' in reference_lines[r] else str(r),
                        prediction_index=p,errors=c) for r,p,c in pairs],
            inversions=inversions,kendall=1-2*inversions/total if total else None)
    return dict(status='optimistic_text_matching_diagnostic_only',modes=results,
                reading_order_certified=False,segmentation_measured=False)


def score_page_text(reference_lines, markdown):
    text, conversion = markdown_text(markdown)
    reference = '\n'.join(line['text'] for line in reference_lines)
    modes = {}
    for name, normalizer in [('strict_NFC',nfc),('strict_NFC_whitespace',_whitespace_only),
                             ('convention_v1',convention),('convention_v2',convention_v2),
                             ('hipe_ocrepair_2026',hipe_ocrepair_2026),('cer_vt',cer_vt)]:
        if name == 'strict_NFC':
            ref, hyp = nfc(reference), nfc(text)
        elif name == 'strict_NFC_whitespace':
            ref, hyp = normalizer(reference), normalizer(text)
        elif name in ('hipe_ocrepair_2026', 'cer_vt'):
            ref, hyp = normalizer(reference), normalizer(text)
        else:
            # La marque terminale de v1/v2 est évaluée AVANT de neutraliser
            # les retours ; aucune correction lexicale ou permutation.
            ref = ' '.join(filter(None,(normalizer(s) for s in reference.splitlines())))
            hyp = ' '.join(filter(None,(normalizer(s) for s in text.splitlines())))
            ref, hyp = re.sub(r'\s+',' ',ref), re.sub(r'\s+',' ',hyp)
        errors = lev(ref,hyp)
        counts = dict(errors=errors,reference_characters=len(ref),prediction_characters=len(hyp),
                      cer=errors/len(ref) if ref else None,exact=ref==hyp)
        try:
            from rapidfuzz.distance import Levenshtein
            ops = Levenshtein.editops(ref,hyp)
            counts.update(substitutions=sum(o.tag=='replace' for o in ops),
                          deletions=sum(o.tag=='delete' for o in ops),
                          insertions=sum(o.tag=='insert' for o in ops))
        except ImportError:
            counts['edit_breakdown_status']='rapidfuzz_unavailable'
        modes[name] = counts
    return dict(text=modes,markdown_conversion=conversion,
                hipe_normalization=dict(source=HIPE_NORMALIZATION_SOURCE,
                    source_sha256=HIPE_NORMALIZATION_SOURCE_SHA256,
                    retrieved='2026-10-07', accents_preserved=True,
                    metric='CER=(substitutions+deletions+insertions)/reference_characters; not cMER'),
                unordered_line_diagnostic=unordered_line_diagnostic(reference_lines,text),
                reference_lines=len(reference_lines),spatial_coverage='not_measured_by_whole_page_VT',
                complete_pipeline_certified=False), text


def evaluate(manifest_path, outputs, split, reference_dpi=None):
    manifest = json.loads(Path(manifest_path).read_text())
    records = []
    for row in manifest['pages']:
        if row['split'] != split:
            continue
        record = {k:row[k] for k in ('id','family','split','human_text')}
        out = Path(outputs)/row['id']
        artifact = out/'vt.gemini.md'
        if not artifact.exists():
            record.update(status='missing_page_transcription',coverage=0,criteria_met=False)
            records.append(record)
            continue
        for key in ('image','reference'):
            if hashlib.sha256(Path(row[key]).read_bytes()).hexdigest() != row[key+'_sha256']:
                raise ValueError('Données modifiées : '+row['id'])
        provenance = json.loads((out/'vt-provenance.json').read_text())
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != provenance['artifact_sha256'] or provenance['image_sha256'] != row['image_sha256']:
            raise ValueError('VT/provenance modifiée : '+row['id'])
        reference,reference_audit=load_page_reference(row['reference'],dpi=reference_dpi)
        metrics, text = score_page_text(reference,artifact.read_text())
        metrics['reference_text_audit']=reference_audit
        metrics.update(artifact_sha256=digest,uncertain=provenance['uncertain'],
                       protocol='PROTOCOLE-VT-PAGE.md',human_text_reference=row['human_text'],
                       text_status='independent_human_reference' if row['human_text'] else 'diagnostic_nonhuman_reference')
        (out/'independent-page-text-scores.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
        (out/'independent-plain-vt.txt').write_text(text)
        record.update(status='measured',uncertain=provenance['uncertain'],metrics=metrics,criteria_met=False,
                      reading_status=provenance.get('reading_status','unspecified'),
                      model_reported_complete=provenance.get('model_reported_complete'),
                      coverage_certified=provenance.get('coverage_certified',False))
        records.append(record)
    return dict(split=split,pages=len(records),rows=records,
                measured=sum(r['status']=='measured' for r in records),
                missing=sum(r['status']!='measured' for r in records),
                protocol_sha256=hashlib.sha256(Path(__file__).resolve().parents[1].joinpath('PROTOCOLE-VT-PAGE.md').read_bytes()).hexdigest(),
                original_suite_protocol_sha256=manifest['protocol_sha256'],criteria_met=False)
