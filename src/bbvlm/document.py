"""Canonical document graph. Coordinates are page pixels, half-open xyxy.

Model proposals never confer human verification. The graph is authoritative;
XML exports are projections and their limitations must remain explicit.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import math
import re
from pathlib import Path

STATUSES = {"automatic", "pending", "ambiguous", "rejected", "human_verified"}
KINDS = {"page", "region", "line", "word"}


def new_document(document_id):
    return {"schema_version": "bbvlm.document/1", "id": document_id,
            "coordinate_system": "page_pixels_xyxy_half_open",
            "nodes": [], "semantic_units": [], "articles": [], "reading_order": [],
            "metadata": [], "events": [], "proposals": []}


def index(document):
    return {n["id"]: n for n in document["nodes"]}


def children(document, parent, kind=None):
    return [n for n in document["nodes"]
            if n.get("parent") == parent and (kind is None or n["kind"] == kind)]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(d)
    return d


def save(document, path):
    validate(document)
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def validate(d):
    errors = []
    if d.get("schema_version") != "bbvlm.document/1":
        raise ValueError("unsupported document schema")
    if d.get("coordinate_system") != "page_pixels_xyxy_half_open":
        errors.append("unsupported coordinate convention")
    nodes = d.get("nodes", [])
    ix = index(d)
    if len(ix) != len(nodes):
        errors.append("duplicate node IDs")
    for n in nodes:
        nid = n.get("id", "")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", nid):
            errors.append(f"invalid XML-compatible ID: {nid}")
        if n.get("kind") not in KINDS or n.get("status") not in STATUSES:
            errors.append(f"invalid kind/status: {nid}")
        box = n.get("bbox")
        if not isinstance(box, (list, tuple)) or len(box) != 4 or not all(
                isinstance(v, (int, float)) and math.isfinite(v) for v in box):
            errors.append(f"invalid bbox: {nid}")
            continue
        if box[0] < 0 or box[1] < 0 or box[2] <= box[0] or box[3] <= box[1]:
            errors.append(f"empty/negative bbox: {nid}")
        if n["kind"] != "page":
            p = ix.get(n.get("parent"))
            expected = {"region": "page", "line": "region", "word": "line"}[n["kind"]]
            if p is None or p["kind"] != expected:
                errors.append(f"invalid parent: {nid}")
            page = ix.get(n.get("page"))
            if page is None or page["kind"] != "page":
                errors.append(f"invalid page: {nid}")
            elif box[2] > page["bbox"][2] or box[3] > page["bbox"][3]:
                errors.append(f"outside page: {nid}")
            if p and p["kind"] != "page" and p.get("page") != n.get("page"):
                errors.append(f"cross-page parent: {nid}")
        for field in ("polygon", "baseline"):
            pts = n.get(field, [])
            if not all(isinstance(p, (tuple, list)) and len(p) == 2 and
                       all(isinstance(v, (int, float)) and math.isfinite(v) for v in p)
                       for p in pts):
                errors.append(f"invalid {field}: {nid}")
    article_ids = set()
    semantic_unit_ids = set()
    for unit in d.get("semantic_units", []):
        uid = unit.get("id", "")
        if uid in semantic_unit_ids or uid in ix:
            errors.append(f"duplicate semantic-unit ID: {uid}")
        semantic_unit_ids.add(uid)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", uid):
            errors.append("invalid semantic-unit ID")
        for rid in unit.get("regions", []):
            if rid not in ix or ix[rid]["kind"] != "region":
                errors.append(f"unknown semantic-unit region: {rid}")
    for a in d.get("articles", []):
        if a["id"] in article_ids or a["id"] in ix:
            errors.append(f"duplicate article ID: {a['id']}")
        article_ids.add(a["id"])
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", a["id"]):
            errors.append("invalid article ID")
        for rid in a.get("regions", []):
            if rid not in ix or ix[rid]["kind"] != "region":
                errors.append(f"unknown article region: {rid}")
    edges = d.get("reading_order", [])
    adjacency = {}
    for edge in edges:
        a, b = edge.get("before"), edge.get("after")
        if a not in ix or b not in ix or a == b:
            errors.append(f"invalid reading-order edge: {a}, {b}")
        elif ix[a]["kind"] != ix[b]["kind"] or ix[a]["kind"] not in {"region", "line"}:
            errors.append(f"mixed reading-order levels: {a}, {b}")
        adjacency.setdefault(a, []).append(b)
    active, done = set(), set()
    def visit(n):
        if n in active:
            raise ValueError("reading-order cycle")
        if n in done:
            return
        active.add(n)
        for nxt in adjacency.get(n, []):
            visit(nxt)
        active.remove(n)
        done.add(n)
    try:
        for n in adjacency:
            visit(n)
    except ValueError as e:
        errors.append(str(e))
    for m in d.get("metadata", []):
        if m.get("category") not in {"observed", "derived", "interpretation"}:
            errors.append("metadata category is required")
        refs = m.get("evidence", [])
        if m.get("category") == "observed" and not refs:
            errors.append("observed metadata requires evidence")
        if any(r not in ix for r in refs):
            errors.append("unknown metadata evidence")
    if errors:
        raise ValueError("; ".join(errors))
    return d


def review_queue(d):
    """Coverage is never improved by dropping a rejected/unaligned line."""
    queue = []
    for n in d["nodes"]:
        if n["kind"] != "line":
            continue
        reasons = list(n.get("issues", []))
        if not n.get("text"):
            reasons.append("missing_transcription")
        if n.get("needs_alignment") or not children(d, n["id"], "word"):
            reasons.append("missing_word_alignment")
        if n["status"] != "human_verified":
            reasons.append("not_human_verified")
        if reasons:
            queue.append({"id": n["id"], "page": n["page"],
                          "bbox": n["bbox"], "reasons": sorted(set(reasons))})
    return queue


def apply_proposal(document, proposal, model, requested_line_ids=None):
    """Atomic application; any changed text invalidates its old word alignment.

    A response must cover exactly its requested line IDs, not a positional list.
    Unchanged text does not upgrade any validation status.
    """
    d = deepcopy(document)
    ix = index(d)
    expected = (list(requested_line_ids) if requested_line_ids is not None else
                [n['id'] for n in document['nodes'] if n['kind'] == 'line'])
    if proposal.get('requested_line_ids') != expected:
        raise ValueError('response batch differs from the trusted request')
    results = proposal.get("lines", [])
    got = [r["id"] for r in results]
    if len(expected) != len(set(expected)) or len(got) != len(set(got)) or set(got) != set(expected):
        raise ValueError("line IDs do not exactly match the requested batch")
    for result in results:
        n = ix.get(result["id"])
        if n is None or n["kind"] != "line" or not isinstance(result.get("text"), str):
            raise ValueError("unknown line or invalid transcription")
        if n["status"] == "human_verified" and n.get("text") != result["text"]:
            raise ValueError("a model cannot overwrite human-verified text")
        if n.get("text") != result["text"]:
            old_words = children(d, n["id"], "word")
            d["events"].append({"action": "replace_transcription", "model": model,
                                "line": n["id"], "previous_text": n.get("text"),
                                "previous_words": deepcopy(old_words)})
            d["nodes"] = [x for x in d["nodes"] if x not in old_words]
            n["text"] = result["text"]
            n["needs_alignment"] = True
            n["status"] = "automatic"
        if result.get("uncertain"):
            if n["status"] != "human_verified":
                n["status"] = "ambiguous"
            n.setdefault("issues", []).append("model_uncertainty")
    for r in proposal.get("regions", []):
        n = ix.get(r["id"])
        if n is None or n["kind"] != "region" or not isinstance(r.get("role"), str):
            raise ValueError("unknown region or invalid role")
        if n['status'] == 'human_verified' and n.get('role') != r['role']:
            raise ValueError('a model cannot overwrite a human-verified region role')
        n["role"] = r["role"]
        n["role_source"] = model
    if "articles" in proposal:
        if any(a.get('status') == 'human_verified' for a in d['articles']):
            raise ValueError('human-verified article structure requires explicit review')
        d["articles"] = [dict(a, status="automatic", source=model) for a in proposal["articles"]]
    if "reading_order" in proposal:
        if any(e.get('status') == 'human_verified' for e in d['reading_order']):
            raise ValueError('human-verified reading order requires explicit review')
        d["reading_order"] = [dict(e, status="automatic", source=model) for e in proposal["reading_order"]]
    for m in proposal.get("metadata", []):
        d["metadata"].append(dict(m, status="automatic", source=model))
    d["proposals"].append({"model": model, "sha256": digest(proposal), "response": proposal})
    validate(d)
    return d
