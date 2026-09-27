"""Optional native PERO adapter. Never guesses crop-to-page transforms.

Run PERO recognition once in an environment containing its models, then retain
PAGE geometry + logits using save_cache(). Re-alignment uses the native exporter.
NPZ/JSON replaces pickle for portable recorded inputs. Model execution is separate.
"""
import hashlib
import json
from pathlib import Path
import numpy as np


def bind_native_alto_ids(xml, regions):
    """Restore IDs omitted by PERO ALTO export under a strict checked contract.

    PERO emits blocks as block_<region.id> and lines in region.lines order.
    Counts, diplomatic text and integer geometry must all agree before binding.
    A changed exporter contract fails rather than guessing correspondence.
    """
    import re
    from lxml import etree as E
    root=E.fromstring(xml,E.XMLParser(resolve_entities=False,no_network=True))
    ns=E.QName(root).namespace;q=lambda n:f'{{{ns}}}{n}'
    blocks=root.findall('.//'+q('TextBlock'))
    by_id={b.get('ID'):b for b in blocks}
    expected={'block_'+r.id for r in regions}
    if len(by_id)!=len(blocks) or set(by_id)!=expected:
        raise ValueError('native ALTO region binding mismatch')
    used={e.get('ID') for e in root.iter() if e.get('ID')}
    for region in regions:
        exported=by_id['block_'+region.id].findall(q('TextLine'))
        if len(exported)!=len(region.lines):
            raise ValueError('native ALTO line count mismatch')
        for element,line in zip(exported,region.lines):
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*',line.id) or line.id in used:
                raise ValueError('invalid or duplicate native line ID')
            words=element.findall(q('String'))
            if ' '.join(w.get('CONTENT','') for w in words)!=line.transcription:
                raise ValueError('native ALTO diplomatic text mismatch')
            pts=np.asarray(line.polygon);lo=pts.min(0);hi=pts.max(0)
            geom=[int(lo[0]),int(lo[1]),int(hi[0]-lo[0]),int(hi[1]-lo[1])]
            if geom!=[int(element.get(k)) for k in ('HPOS','VPOS','WIDTH','HEIGHT')]:
                raise ValueError('native ALTO line geometry mismatch')
            element.set('ID',line.id);used.add(line.id)
            for i,w in enumerate(words,1):
                wid=f'{line.id}_W{i:04d}'
                if wid in used:raise ValueError('native word ID collision')
                w.set('ID',wid);used.add(wid)
    return E.tostring(root,pretty_print=True,xml_declaration=True,encoding='utf-8')


def save_cache(layout, directory, model_id):
    out = Path(directory); out.mkdir(parents=True, exist_ok=True)
    page = out/"layout.xml"
    layout.to_pagexml(str(page))
    arrays, entries = {}, []
    for i, line in enumerate(layout.lines_iterator()):
        if line.logits is None or line.characters is None or line.logit_coords is None:
            raise ValueError(f"missing recognition cache for {line.id}")
        key = f"line_{i}"
        arrays[key] = line.logits.toarray() if hasattr(line.logits, "toarray") else np.asarray(line.logits)
        entries.append({"id": line.id, "key": key, "characters": list(line.characters),
                        "logit_coords": list(line.logit_coords)})
    np.savez_compressed(out/"logits.npz", **arrays)
    meta = {"format": "bbvlm.pero-cache/1", "model_id": model_id,
            "page_sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
            "logits_sha256": hashlib.sha256((out/"logits.npz").read_bytes()).hexdigest(),
            "lines": entries}
    (out/"cache.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_cache(directory):
    from pero_ocr.core.layout import PageLayout
    from scipy.sparse import csc_matrix
    out = Path(directory)
    meta = json.loads((out/"cache.json").read_text(encoding="utf-8"))
    if meta.get("format") != "bbvlm.pero-cache/1":
        raise ValueError("unknown cache format")
    for filename, field in [("layout.xml", "page_sha256"), ("logits.npz", "logits_sha256")]:
        if hashlib.sha256((out/filename).read_bytes()).hexdigest() != meta[field]:
            raise ValueError("cache geometry/logits changed: "+filename)
    layout = PageLayout(file=str(out/"layout.xml"))
    ix = {l.id: l for l in layout.lines_iterator()}
    if set(ix) != {r["id"] for r in meta["lines"]}:
        raise ValueError("cached line IDs differ from PAGE geometry")
    with np.load(out/"logits.npz", allow_pickle=False) as arrays:
        for item in meta["lines"]:
            line = ix[item["id"]]
            line.logits = csc_matrix(arrays[item["key"]])
            line.characters = item["characters"]
            line.logit_coords = item["logit_coords"]
    return layout, meta


def realign(layout, transcriptions):
    """All line IDs required. Fail explicitly instead of silently substituting.

    Returns native ALTO and a report. A native zero-confidence/fallback signal is
    recorded; callers must not treat those boxes as validated ground truth.
    """
    from pero_ocr.core.force_alignment import align_text
    lines = list(layout.lines_iterator())
    if set(transcriptions) != {l.id for l in lines}:
        raise ValueError("transcriptions must cover exactly the cached line IDs")
    for line in lines:
        text = transcriptions[line.id]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"empty/invalid transcription: {line.id}")
        if any(c.isspace() and c != ' ' for c in text):
            raise ValueError(f"unsupported whitespace: {line.id}")
        codec = {c: i for i, c in enumerate(line.characters)}
        blank = line.logits.shape[1]-1
        unknown = {c for c in text if c not in codec or codec[c] >= blank}
        if unknown:
            raise ValueError(f"unsupported characters in {line.id}: {sorted(unknown)}")
        logp = line.get_full_logprobs()[line.logit_coords[0]:line.logit_coords[1]]
        align_text(-logp, np.array([codec[c] for c in text]), blank)
    for line in lines:
        line.transcription = transcriptions[line.id]
    xml = layout.to_altoxml_string()
    if isinstance(xml, str):
        xml = xml.encode("utf-8")
    xml = bind_native_alto_ids(xml, layout.regions)
    report = {"engine": "PERO native forced alignment and crop projection",
              "ids_bound_with_text_count_geometry_checks": True,
              "recognition_recomputed": False,
              "lines": [{"id": l.id, "native_confidence": float(l.transcription_confidence)
                          if l.transcription_confidence is not None else None,
                          "requires_review": bool(l.transcription_confidence is None or l.transcription_confidence == 0)}
                         for l in lines], "certified_ground_truth": False}
    return xml, report
