"""Explicit ALTO/PAGE imports and a documented ALTO 4.4 / METS 1.12 profile.

Imports retain the source XML for attributes outside this initial graph profile.
Exports are normalized projections, not lossless replacements of arbitrary XML.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import mimetypes
import re
from urllib.parse import urlparse
from datetime import datetime, timezone
from lxml import etree as E
from .document import new_document, children, validate

ALTO = "http://www.loc.gov/standards/alto/ns-v4#"
METS = "http://www.loc.gov/METS/"
XLINK = "http://www.w3.org/1999/xlink"
MODS = "http://www.loc.gov/mods/v3"
PREMIS = "http://www.loc.gov/premis/v3"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
BB = "https://github.com/maribakulj/BBVLM/ns/1"
PARSER = E.XMLParser(resolve_entities=False, no_network=True)


def tag(ns, name):
    return f"{{{ns}}}{name}"


def sub(parent, ns, element_name, text=None, **attrs):
    n = E.SubElement(parent, tag(ns, element_name), **{k: str(v) for k, v in attrs.items()})
    if text is not None:
        n.text = str(text)
    return n


def xyxy(el):
    x, y, w, h = [float(el.get(a)) for a in ("HPOS", "VPOS", "WIDTH", "HEIGHT")]
    return [x, y, x+w, y+h]


def points(value):
    if not value:
        return []
    nums = [float(x) for x in re.split(r"[\s,]+", value.strip())]
    if len(nums) % 2:
        raise ValueError("odd number of polygon coordinates")
    return [nums[i:i+2] for i in range(0, len(nums), 2)]


def bounds(pts):
    return [min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts)]


def import_xml(path, document_id=None):
    raw = Path(path).read_bytes()
    root = E.fromstring(raw, PARSER)
    d = new_document(document_id or Path(path).stem)
    d["source"] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                   "xml": raw.decode("utf-8-sig")}
    ns = E.QName(root).namespace
    q = lambda name: tag(ns, name)
    is_alto = E.QName(root).localname == "alto"
    if not is_alto and E.QName(root).localname != "PcGts":
        raise ValueError("expected ALTO or PAGE XML")
    if is_alto:
        unit = root.findtext(".//"+q("MeasurementUnit"))
        if unit != "pixel":
            raise ValueError("ALTO import requires pixel units; convert explicitly first")
    def node(nid, kind, parent, page, box, el=None, **extra):
        n = {"id": nid, "kind": kind, "parent": parent, "page": page,
             "bbox": box, "status": "automatic", **extra}
        if el is not None:
            n["source_id"] = el.get("ID") if is_alto else el.get("id")
            n["source_attributes"] = dict(el.attrib)
        d["nodes"].append(n)
        return n
    source_orders = {}
    semantic_groups = {}
    order_warnings = []
    for pi, page in enumerate(root.iter(q("Page")), 1):
        pid = f"P{pi:04d}"
        w = float(page.get("WIDTH" if is_alto else "imageWidth"))
        h = float(page.get("HEIGHT" if is_alto else "imageHeight"))
        source_image = (root.findtext(".//"+q("fileName")) if is_alto else page.get("imageFilename")) or ""
        node(pid, "page", None, pid, [0, 0, w, h], page, image=source_image)
        region_names = {"TextBlock", "Illustration", "GraphicalElement"} if is_alto else {
            "TextRegion", "ImageRegion", "GraphicRegion", "TableRegion", "SeparatorRegion"}
        for ri, reg in enumerate((r for r in page.iter() if isinstance(r.tag, str) and E.QName(r).localname in region_names), 1):
            rid = f"{pid}_R{ri:04d}"
            reg_kind = E.QName(reg).localname
            poly = reg.find(q("Shape")+"/"+q("Polygon")) if is_alto else reg.find(q("Coords"))
            pts = points(poly.get("POINTS" if is_alto else "points")) if poly is not None else []
            box = xyxy(reg) if is_alto else bounds(pts)
            role = "body" if reg_kind in {"TextBlock", "TextRegion"} else reg_kind
            if is_alto and reg.get("BLOCK_TYPE"):
                role = reg.get("BLOCK_TYPE").lower()
            rn = node(rid, "region", pid, pid, box, reg, polygon=pts, role=role)
            if is_alto and reg.get("SSU_ID"):
                source_ssu = reg.get("SSU_ID")
                rn["source_semantic_unit"] = source_ssu
                semantic_groups.setdefault((pid, source_ssu), []).append(rid)
            if is_alto and reg.get("READING_ORDER") not in (None, ""):
                try:
                    source_order = int(reg.get("READING_ORDER"))
                    rn["source_reading_order"] = source_order
                    if source_order >= 0:
                        source_orders.setdefault(pid, []).append((source_order, rid))
                except ValueError:
                    order_warnings.append({"page": pid, "region": rid, "value": reg.get("READING_ORDER")})
            for li, line in enumerate(reg.findall(q("TextLine")), 1):
                lid = f"{rid}_L{li:04d}"
                poly = line.find(q("Shape")+"/"+q("Polygon")) if is_alto else line.find(q("Coords"))
                pts = points(poly.get("POINTS" if is_alto else "points")) if poly is not None else []
                words = line.findall(q("String" if is_alto else "Word"))
                texts = [a.get("CONTENT", "") if is_alto else a.findtext(q("TextEquiv")+"/"+q("Unicode"), "") for a in words]
                text = " ".join(texts) if is_alto else line.findtext(q("TextEquiv")+"/"+q("Unicode"), "")
                if is_alto:
                    try:
                        box = xyxy(line)
                    except (TypeError, ValueError):
                        boxes = [xyxy(a) for a in words]
                        box = bounds([[b[0], b[1]] for b in boxes]+[[b[2], b[3]] for b in boxes])
                    baseline_attr = line.get("BASELINE", "")
                    if baseline_attr and len(re.split(r"[\s,]+", baseline_attr.strip())) == 1:
                        base = [[box[0], float(baseline_attr)], [box[2], float(baseline_attr)]]
                    else:
                        base = points(baseline_attr)
                else:
                    box = bounds(pts)
                    bl = line.find(q("Baseline"))
                    base = points(bl.get("points")) if bl is not None else []
                ln = node(lid, "line", rid, pid, box, line, polygon=pts, baseline=base,
                          text=text, needs_alignment=not bool(words))
                for wi, word in enumerate(words, 1):
                    wp = word.find(q("Coords")) if not is_alto else None
                    try:
                        wb = xyxy(word) if is_alto else bounds(points(wp.get("points")))
                    except (TypeError, ValueError, AttributeError):
                        ln["needs_alignment"] = True
                        continue
                    wn = node(f"{lid}_W{wi:04d}", "word", lid, pid, wb, word,
                              text=texts[wi-1])
                    if is_alto:
                        for a in ("WC", "SUBS_TYPE", "SUBS_CONTENT"):
                            if word.get(a) is not None:
                                wn[a] = word.get(a)
    for i, ((pid, source_ssu), regions) in enumerate(sorted(semantic_groups.items()), 1):
        d["semantic_units"].append({
            "id": f"SU{i:05d}", "label": source_ssu, "page": pid,
            "regions": regions, "status": "automatic", "source": "distributed_alto"
        })
    for pid, ordered in source_orders.items():
        values = [value for value, _ in ordered]
        if len(values) != len(set(values)):
            order_warnings.append({"page": pid, "issue": "duplicate_nonnegative_source_order"})
            continue
        ids = [rid for _, rid in sorted(ordered)]
        d["reading_order"].extend(
            {"before": a, "after": b, "status": "automatic", "source": "distributed_alto"}
            for a, b in zip(ids, ids[1:])
        )
    d["events"].append({"action": "import", "format": "ALTO" if is_alto else "PAGE",
                        "source_sha256": d["source"]["sha256"],
                        "note": "source XML order retained; explicit non-negative region order and SSU labels imported as automatic evidence, not human verification",
                        "reading_order_warnings": order_warnings})
    return validate(d)


def geom(box):
    x, y, xx, yy = box
    fmt = lambda v: f"{v:g}"
    return dict(HPOS=fmt(x), VPOS=fmt(y), WIDTH=fmt(xx-x), HEIGHT=fmt(yy-y))


def shape(parent, pts):
    if pts:
        sub(sub(parent, ALTO, "Shape"), ALTO, "Polygon",
            POINTS=" ".join(f"{x:g},{y:g}" for x, y in pts))


def explicit_total_order(d, page_id):
    """Export only a uniquely determined complete region order.

    A partial DAG remains in document.json; silently filling its gaps would
    convert unknown order into invented certainty.
    """
    ids = {n['id'] for n in children(d, page_id, 'region')}
    if len(ids) < 2:
        return []
    edges = {(e['before'], e['after']) for e in d.get('reading_order', [])
             if e['before'] in ids and e['after'] in ids}
    pending, order = set(ids), []
    while pending:
        ready = [n for n in pending if not any(b == n and a in pending for a, b in edges)]
        if len(ready) != 1:
            return []
        order.append(ready[0]); pending.remove(ready[0])
    return order


def export_alto(d, page_id):
    validate(d)
    pages = [n for n in d["nodes"] if n["kind"] == "page" and n["id"] == page_id]
    if len(pages) != 1:
        raise ValueError("unknown page")
    page = pages[0]
    root = E.Element(tag(ALTO, "alto"), nsmap={None: ALTO})
    desc = sub(root, ALTO, "Description")
    sub(desc, ALTO, "MeasurementUnit", "pixel")
    sub(sub(desc, ALTO, "sourceImageInformation"), ALTO, "fileName", page.get("image", ""))
    proc = sub(desc, ALTO, "Processing", ID="BBVLM_PROCESS")
    sub(proc, ALTO, "processingStepDescription", "BBVLM draft projection. Unaligned lines have one tagged String without word geometry. Consult document.json and review.json; not certified ground truth.")
    sub(sub(proc, ALTO, "processingSoftware"), ALTO, "softwareName", "BBVLM document/1")
    tags = sub(root, ALTO, "Tags")
    for s in sorted({n["status"] for n in d["nodes"]}):
        sub(tags, ALTO, "OtherTag", ID="STATUS_"+s, LABEL=s, TYPE="validation_status")
    sub(tags, ALTO, "OtherTag", ID="UNALIGNED", LABEL="line_without_word_alignment", TYPE="geometry_status")
    region_roles = {}
    for i, reg in enumerate(children(d, page_id, 'region'), 1):
        if reg.get('role'):
            region_roles[reg['id']] = f'ROLE_{i}'
            sub(tags, ALTO, 'RoleTag', ID=f'ROLE_{i}', LABEL=reg['role'])
    order = explicit_total_order(d, page_id)
    if order:
        ro = sub(root, ALTO, 'ReadingOrder')
        group = sub(ro, ALTO, 'OrderedGroup', ID='BBVLM_READING_ORDER')
        for i, ref in enumerate(order, 1):
            sub(group, ALTO, 'ElementRef', ID=f'BBVLM_REF_{i}', REF=ref)
    layout = sub(root, ALTO, "Layout")
    p = sub(layout, ALTO, "Page", ID=page_id, PHYSICAL_IMG_NR="1",
            WIDTH=f"{page['bbox'][2]:g}", HEIGHT=f"{page['bbox'][3]:g}")
    space = sub(p, ALTO, "PrintSpace", ID=page_id+"_PS", **geom(page["bbox"]))
    for reg in children(d, page_id, "region"):
        lines = children(d, reg["id"], "line")
        graphic = reg.get("role") in {"ImageRegion", "Illustration", "GraphicRegion", "GraphicalElement", "SeparatorRegion"} and not lines
        rt = "Illustration" if graphic else "TextBlock"
        refs = 'STATUS_'+reg['status']
        if reg['id'] in region_roles:
            refs += ' '+region_roles[reg['id']]
        block = sub(space, ALTO, rt, ID=reg["id"], TAGREFS=refs, **geom(reg["bbox"]))
        shape(block, reg.get("polygon"))
        for line in lines:
            at = dict(ID=line["id"], TAGREFS="STATUS_"+line["status"], **geom(line["bbox"]))
            if line.get("baseline"):
                at["BASELINE"] = " ".join(f"{x:g},{y:g}" for x, y in line["baseline"])
            ln = sub(block, ALTO, "TextLine", **at)
            shape(ln, line.get("polygon"))
            words = children(d, line["id"], "word")
            if not words or line.get("needs_alignment"):
                sub(ln, ALTO, "String", ID=line["id"]+"_UNALIGNED", CONTENT=line.get("text", ""), TAGREFS="UNALIGNED")
            else:
                for word in words:
                    wa = {a: word[a] for a in ("WC", "SUBS_TYPE", "SUBS_CONTENT") if a in word}
                    sub(ln, ALTO, "String", ID=word["id"], CONTENT=word["text"], **geom(word["bbox"]), **wa)
    return E.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True)


def _mods_projection(d):
    """Conservative MODS 3.8 projection; evidence remains in BBVLM metadata."""
    mods = E.Element(tag(MODS, 'mods'), version='3.8')
    sub(mods, MODS, 'identifier', d['id'], type='local')
    for m in d.get('metadata', []):
        field, value = m['field'].lower(), m['value']
        if field in {'title', 'label'}:
            sub(sub(mods, MODS, 'titleInfo'), MODS, 'title', value)
        elif field in {'creator', 'author'}:
            name = sub(mods, MODS, 'name', type='personal')
            sub(name, MODS, 'namePart', value)
            role = sub(name, MODS, 'role')
            sub(role, MODS, 'roleTerm', 'creator', type='text')
        elif field in {'date', 'date_issued', 'dateissued'}:
            sub(sub(mods, MODS, 'originInfo'), MODS, 'dateIssued', value)
        elif field == 'publisher':
            sub(sub(mods, MODS, 'originInfo'), MODS, 'publisher', value)
        elif field in {'language', 'language_text'}:
            sub(sub(mods, MODS, 'language'), MODS, 'languageTerm', value, type='text')
        elif field == 'identifier':
            sub(mods, MODS, 'identifier', value, type='local')
        else:
            sub(mods, MODS, 'note', value, displayLabel=m['field'])
    info = sub(mods, MODS, 'recordInfo')
    sub(info, MODS, 'recordContentSource', 'BBVLM automatic projection')
    sub(info, MODS, 'recordOrigin',
        'Generated from evidence-typed document metadata; not a cataloguing authority record.')
    return mods


def _premis_projection(file_records):
    """PREMIS 3 file fixity plus one software export event."""
    premis = E.Element(tag(PREMIS, 'premis'), version='3.0')
    for fid, record in file_records.items():
        if not record.get('checksum'):
            continue
        obj = sub(premis, PREMIS, 'object', **{tag(XSI, 'type'): 'premis:file'})
        ident = sub(obj, PREMIS, 'objectIdentifier')
        sub(ident, PREMIS, 'objectIdentifierType', 'BBVLM METS file ID')
        sub(ident, PREMIS, 'objectIdentifierValue', fid)
        chars = sub(obj, PREMIS, 'objectCharacteristics')
        fix = sub(chars, PREMIS, 'fixity')
        sub(fix, PREMIS, 'messageDigestAlgorithm', 'SHA-256')
        sub(fix, PREMIS, 'messageDigest', record['checksum'])
        if record.get('size') is not None:
            sub(chars, PREMIS, 'size', record['size'])
        designation = sub(sub(chars, PREMIS, 'format'), PREMIS, 'formatDesignation')
        sub(designation, PREMIS, 'formatName', record['mimetype'])
        sub(obj, PREMIS, 'originalName', record['href'])
    event = sub(premis, PREMIS, 'event')
    ident = sub(event, PREMIS, 'eventIdentifier')
    sub(ident, PREMIS, 'eventIdentifierType', 'BBVLM event')
    sub(ident, PREMIS, 'eventIdentifierValue', 'BBVLM_PACKAGE_EXPORT')
    sub(event, PREMIS, 'eventType', 'metadata extraction')
    sub(event, PREMIS, 'eventDateTime', datetime.now(timezone.utc).isoformat())
    detail = sub(event, PREMIS, 'eventDetailInformation')
    sub(detail, PREMIS, 'eventDetail',
        'Automatic ALTO/METS package export; validation does not certify ground truth.')
    agent = sub(premis, PREMIS, 'agent')
    ident = sub(agent, PREMIS, 'agentIdentifier')
    sub(ident, PREMIS, 'agentIdentifierType', 'software name')
    sub(ident, PREMIS, 'agentIdentifierValue', 'BBVLM document/1')
    sub(agent, PREMIS, 'agentName', 'BBVLM')
    sub(agent, PREMIS, 'agentType', 'software')
    return premis


def export_mets(d, alto_files, graph_file="document.json", retrieval_file=None,
                file_records=None):
    """METS 1.12: logical article divisions point to physical ALTO regions.

    Descriptive facts stay in explicit custom metadata with evidence, rather than
    pretending an unvalidated normalized value is a cataloguing authority.
    """
    validate(d)
    file_records = file_records or {}
    root = E.Element(tag(METS, "mets"), nsmap={"mets": METS, "xlink": XLINK,
        "mods": MODS, "premis": PREMIS, "xsi": XSI, "bbvlm": BB}, OBJID=d["id"])
    mods_sec = sub(root, METS, 'dmdSec', ID='DMD_MODS')
    mods_wrap = sub(mods_sec, METS, 'mdWrap', MDTYPE='MODS', MDTYPEVERSION='3.8')
    sub(mods_wrap, METS, 'xmlData').append(_mods_projection(d))
    dm = sub(root, METS, "dmdSec", ID="DMD_EVIDENCE")
    wrap = sub(dm, METS, "mdWrap", MDTYPE="OTHER", OTHERMDTYPE="BBVLM-EVIDENCE-1")
    data = sub(wrap, METS, "xmlData")
    facts = sub(data, BB, "metadata")
    for m in d.get("metadata", []):
        fact = sub(facts, BB, "field", name=m["field"], category=m["category"],
                   status=m.get("status", "automatic"), source=m.get("source", "unknown"))
        sub(fact, BB, "value", m["value"])
        for ref in m.get("evidence", []):
            sub(fact, BB, "evidence", ref=ref)
    premis_records = dict(file_records)
    for page in [n for n in d['nodes'] if n['kind'] == 'page']:
        if page.get('image_sha256'):
            href = page.get('image', '')
            premis_records['FILE_IMAGE_'+page['id']] = {
                'href': href,
                'mimetype': mimetypes.guess_type(urlparse(href).path)[0] or 'application/octet-stream',
                'checksum': page['image_sha256'], 'size': page.get('image_size_bytes')}
    amd = sub(root, METS, 'amdSec', ID='AMD_PACKAGE')
    prov = sub(amd, METS, 'digiprovMD', ID='AMD_PREMIS')
    # A PREMIS container mixes Object, Event and Agent entities, so it must not
    # be mislabeled as the narrower METS MDTYPE PREMIS:OBJECT.
    prov_wrap = sub(prov, METS, 'mdWrap', MDTYPE='OTHER',
                    OTHERMDTYPE='PREMIS:3.0', MDTYPEVERSION='3.0')
    sub(prov_wrap, METS, 'xmlData').append(_premis_projection(premis_records))
    fs = sub(root, METS, "fileSec")
    fg = sub(fs, METS, "fileGrp", USE="OCR")
    for pid, filename in alto_files.items():
        record = file_records.get('FILE_'+pid, {})
        attrs = dict(ID='FILE_'+pid, MIMETYPE=record.get('mimetype', 'application/xml'), ADMID='AMD_PREMIS')
        if record.get('checksum'):
            attrs.update(SIZE=record['size'], CHECKSUM=record['checksum'], CHECKSUMTYPE='SHA-256')
        file = sub(fg, METS, "file", **attrs)
        sub(file, METS, "FLocat", LOCTYPE="URL", **{tag(XLINK, "href"): filename})
    images = sub(fs, METS, 'fileGrp', USE='MASTER_IMAGE')
    for page in [n for n in d['nodes'] if n['kind'] == 'page']:
        href = page.get('image', '')
        mime = mimetypes.guess_type(urlparse(href).path)[0] or 'application/octet-stream'
        attrs = dict(ID='FILE_IMAGE_'+page['id'], MIMETYPE=mime)
        if page.get('image_sha256'):
            attrs.update(CHECKSUM=page['image_sha256'], CHECKSUMTYPE='SHA-256')
        if page.get('image_size_bytes') is not None:
            attrs['SIZE'] = page['image_size_bytes']
        f = sub(images, METS, 'file', **attrs)
        sub(f, METS, 'FLocat', LOCTYPE='URL', **{tag(XLINK, 'href'): href})
    graph_group = sub(fs, METS, "fileGrp", USE="DOCUMENT_GRAPH")
    record = file_records.get('FILE_GRAPH', {})
    attrs = dict(ID='FILE_GRAPH', MIMETYPE='application/json', ADMID='AMD_PREMIS')
    if record.get('checksum'):
        attrs.update(SIZE=record['size'], CHECKSUM=record['checksum'], CHECKSUMTYPE='SHA-256')
    file = sub(graph_group, METS, "file", **attrs)
    sub(file, METS, "FLocat", LOCTYPE="URL", **{tag(XLINK, "href"): graph_file})
    if retrieval_file:
        group = sub(fs, METS, "fileGrp", USE="RETRIEVAL_INDEX")
        record = file_records.get('FILE_RETRIEVAL', {})
        attrs = dict(ID='FILE_RETRIEVAL', MIMETYPE='application/vnd.sqlite3', ADMID='AMD_PREMIS')
        if record.get('checksum'):
            attrs.update(SIZE=record['size'], CHECKSUM=record['checksum'], CHECKSUMTYPE='SHA-256')
        f = sub(group, METS, "file", **attrs)
        sub(f, METS, "FLocat", LOCTYPE="URL", **{tag(XLINK, "href"): retrieval_file})
    dmdids = 'DMD_MODS DMD_EVIDENCE'
    phys = sub(sub(root, METS, "structMap", TYPE="PHYSICAL"), METS, "div", TYPE="document", DMDID=dmdids)
    for page in [n for n in d["nodes"] if n["kind"] == "page"]:
        div = sub(phys, METS, "div", ID="PHYS_"+page["id"], TYPE="page")
        sub(div, METS, 'fptr', FILEID='FILE_IMAGE_'+page['id'])
        sub(div, METS, "fptr", FILEID="FILE_"+page["id"])
    logical = sub(sub(root, METS, "structMap", TYPE="LOGICAL"), METS, "div", TYPE="document", DMDID=dmdids)
    ix = {n["id"]: n for n in d["nodes"]}
    for unit in d.get("semantic_units", []):
        div = sub(logical, METS, "div", ID="LOG_"+unit["id"], TYPE="semantic-unit", LABEL=unit.get("label", ""))
        for rid in unit["regions"]:
            sub(sub(div, METS, "fptr"), METS, "area", FILEID="FILE_"+ix[rid]["page"], BETYPE="IDREF", BEGIN=rid)
    for a in d.get("articles", []):
        div = sub(logical, METS, "div", ID="LOG_"+a["id"], TYPE="article", LABEL=a.get("title", ""))
        for rid in a["regions"]:
            sub(sub(div, METS, "fptr"), METS, "area", FILEID="FILE_"+ix[rid]["page"], BETYPE="IDREF", BEGIN=rid)
    return E.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True)


def audit_mets_package(xml, directory):
    """Resolve METS IDs and verify every checksummed local payload."""
    root = E.fromstring(xml, PARSER); directory = Path(directory)
    ids = {v for v in root.xpath('//@ID')}
    files = {f.get('ID'): f for f in root.findall('.//'+tag(METS, 'file'))}
    errors = []
    for attr in ('DMDID', 'ADMID'):
        for value in root.xpath('//@'+attr):
            errors.extend(f'unresolved {attr}: {ref}' for ref in value.split() if ref not in ids)
    for ref in root.xpath('//@FILEID'):
        if ref not in files:
            errors.append('unresolved FILEID: '+ref)
    verified = external = external_checksums = unresolved = 0
    for fid, f in files.items():
        loc = f.find(tag(METS, 'FLocat'))
        href = loc.get(tag(XLINK, 'href')) if loc is not None else None
        if href is None:
            errors.append('missing FLocat: '+fid); continue
        if urlparse(href).scheme in {'http', 'https'}:
            external += 1
            if f.get('CHECKSUM'):
                external_checksums += 1
            continue
        path = directory / href
        if not path.is_file():
            unresolved += 1
            if f.get('CHECKSUM'):
                errors.append('missing checksummed file: '+href)
            continue
        if f.get('CHECKSUM'):
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != f.get('CHECKSUM') or int(f.get('SIZE', -1)) != path.stat().st_size:
                errors.append('fixity mismatch: '+href)
            else:
                verified += 1
    uses = {grp.get('USE'): {f.get('ID') for f in grp.findall(tag(METS, 'file'))}
            for grp in root.findall('.//'+tag(METS, 'fileGrp'))}
    for div in root.findall(".//"+tag(METS, 'structMap')+"[@TYPE='PHYSICAL']//"+tag(METS, 'div')+"[@TYPE='page']"):
        refs = {p.get('FILEID') for p in div.findall(tag(METS, 'fptr'))}
        if not refs.intersection(uses.get('MASTER_IMAGE', set())) or not refs.intersection(uses.get('OCR', set())):
            errors.append('physical page lacks image or OCR pointer: '+str(div.get('ID')))
    if errors:
        raise ValueError('; '.join(errors))
    return {'files': len(files), 'checksums_verified': verified,
            'external_uris': external, 'external_checksum_declarations': external_checksums,
            'unresolved_unchecksummed_local_uris': unresolved,
            'all_idrefs_resolve': True, 'physical_pages_link_image_and_ocr': True}


class LocalSchemaResolver(E.Resolver):
    def __init__(self, directory):
        self.directory = Path(directory)
    def resolve(self, url, pubid, context):
        name = url.rsplit("/", 1)[-1]
        p = self.directory/name
        if p.is_file():
            return self.resolve_filename(str(p), context)
        raise ValueError(f"schema dependency not available offline: {name}")


def validate_xml(xml, schema):
    parser = E.XMLParser(resolve_entities=False, no_network=True)
    parser.resolvers.add(LocalSchemaResolver(Path(schema).resolve().parent))
    validator = E.XMLSchema(E.parse(str(Path(schema).resolve()), parser))
    instance = E.fromstring(xml, PARSER)
    if Path(schema).name == 'mets.xsd':
        # METS 1.12 does not import every permitted extension schema.  Validate
        # its core after removing only foreign xsi:type declarations, then use
        # validate_embedded_profiles for the foreign records themselves.
        instance = deepcopy(instance)
        for element in instance.iter():
            if E.QName(element).namespace != METS:
                element.attrib.pop(tag(XSI, 'type'), None)
    validator.assertValid(instance)
    return True


def validate_embedded_profiles(mets_xml, schemas):
    """Validate PREMIS 3 independently and audit the local MODS 3.8 profile."""
    root = E.fromstring(mets_xml, PARSER); schemas = Path(schemas)
    premis = root.find('.//'+tag(PREMIS, 'premis'))
    mods = root.find('.//'+tag(MODS, 'mods'))
    if premis is None or mods is None:
        raise ValueError('METS must embed both MODS and PREMIS records')
    validate_xml(E.tostring(premis), schemas/'premis-v3-0.xsd')
    if mods.get('version') != '3.8' or mods.find(tag(MODS, 'identifier')) is None:
        raise ValueError('MODS 3.8 local profile requires a document identifier')
    mods_schema = schemas/'mods-3-8.xsd'
    mods_xsd = False
    if mods_schema.is_file():
        validate_xml(E.tostring(mods), mods_schema); mods_xsd = True
    return {'mets_core_xsd_valid': True, 'premis_3_xsd_valid': True,
            'mods_3_8_local_profile_valid': True,
            'mods_3_8_xsd_valid': mods_xsd}
