"""Bridge from Kraken segmentation and existing readers/boxers to the graph.

Segmentation and recognition dependencies are imported only at runtime.
An ID-aware reader may batch within a region. A positional legacy reader is
restricted to one line per call: line count alone cannot validate association.
"""
from pathlib import Path
import time
import json
from PIL import Image, ImageDraw
from .document import new_document, index, validate, review_queue
from .__main__ import export_package


def segmentation_graph(seg, width, height, image_name):
    d = new_document(Path(image_name).stem)
    d["nodes"].append({"id": "P1", "kind": "page", "parent": None, "page": "P1",
                       "bbox": [0, 0, width, height], "image": image_name, "status": "automatic"})
    regions = {}
    region_roles = {}
    for role, group in getattr(seg, "regions", {}).items():
        for reg in group:
            pts = [[float(x), float(y)] for x, y in reg.boundary]
            regions[reg.id] = pts
            region_roles[reg.id] = role
    region_nodes = {}
    for source_id, pts in regions.items():
        rid = f"R{len(region_nodes)+1:04d}"
        region_nodes[source_id] = rid
        d["nodes"].append({"id": rid, "kind": "region", "parent": "P1", "page": "P1",
                           "bbox": [min(x for x,y in pts), min(y for x,y in pts),
                                    max(x for x,y in pts), max(y for x,y in pts)],
                           "polygon": pts, "source_id": source_id, "status": "automatic",
                           "role": region_roles[source_id]})
    for i, line in enumerate(seg.lines, 1):
        pts = [[float(x), float(y)] for x, y in line.boundary]
        box = [min(x for x,y in pts), min(y for x,y in pts), max(x for x,y in pts), max(y for x,y in pts)]
        memberships = list(getattr(line, "regions", None) or [])
        source_region = next((r for r in memberships if r in regions), None)
        # Without a region assignment retain a separate unresolved block.
        key = source_region or f"unassigned_line_{i}"
        if key not in region_nodes:
            rid = f"R{len(region_nodes)+1:04d}"
            rp = regions.get(source_region, pts)
            rb = [min(x for x,y in rp), min(y for x,y in rp), max(x for x,y in rp), max(y for x,y in rp)]
            region_nodes[key] = rid
            d["nodes"].append({"id": rid, "kind": "region", "parent": "P1", "page": "P1",
                               "bbox": rb, "polygon": rp, "status": "automatic",
                               "source_id": source_region, "role": "unclassified"})
        d["nodes"].append({"id": f"L{i:04d}", "kind": "line", "parent": region_nodes[key],
                           "page": "P1", "bbox": box, "polygon": pts,
                           "baseline": [[float(x),float(y)] for x,y in line.baseline],
                           "source_id": line.id, "source_regions": memberships,
                           "text": "", "status": "pending", "needs_alignment": True})
    d["events"].append({"action": "segmentation", "engine": "kraken",
                        "reading_order": "segmentation sequence retained; not certified"})
    return validate(d)


def produce(image, output, reader, boxer, max_lines=None, batch_size=20, verbose=True,
            segmentation=None, cost_function=None):
    import numpy as np
    if max_lines is not None and max_lines < 0 or batch_size <= 0:
        raise ValueError("invalid line limit or batch size")
    pil = Image.open(image).convert("RGB")
    gray = np.asarray(pil.convert("L"))
    if segmentation is None:
        from kraken import blla
        segmentation = blla.segment(pil.convert("L"))
    d = segmentation_graph(segmentation, pil.width, pil.height, Path(image).name)
    nodes = index(d)
    all_lines = [n for n in d["nodes"] if n["kind"] == "line"]
    lines = all_lines if max_lines is None else all_lines[:max_lines]
    batches = []
    id_aware = bool(getattr(reader, "returns_ids", False))
    for n in lines:
        if not id_aware or not batches or len(batches[-1]) >= batch_size or batches[-1][-1]["parent"] != n["parent"]:
            batches.append([])
        batches[-1].append(n)
    start = time.monotonic()
    for batch in batches:
        bb = [min(n["bbox"][0] for n in batch), min(n["bbox"][1] for n in batch),
              max(n["bbox"][2] for n in batch), max(n["bbox"][3] for n in batch)]
        ids = [n["id"] for n in batch]
        try:
            got, quality = reader(pil.crop(tuple(bb)), ids if id_aware else 1)
            if id_aware:
                if not isinstance(got, dict) or set(got) != set(ids):
                    raise ValueError("response line IDs differ from request")
            else:
                if not isinstance(got, (list, tuple)) or len(got) != 1:
                    raise ValueError("positional reader must return exactly one line")
                got = {ids[0]: got[0]}
            if not all(isinstance(t, str) for t in got.values()):
                raise ValueError("reader text must be a string")
        except Exception as error:
            for n in batch:
                n["status"] = "rejected"; n.setdefault("issues", []).append("reader_failure:"+type(error).__name__)
            d["events"].append({"action": "read_failure", "lines": ids, "error": str(error)})
            continue
        d["events"].append({"action": "read", "lines": ids, "reader": getattr(reader, "nom", "unknown"),
                            "quality_reported": quality, "id_aware": id_aware})
        for n in batch:
            text = got[n["id"]]; n["text"] = text
            if not text.strip():
                n["status"] = "ambiguous"; n.setdefault("issues", []).append("empty_reading")
                continue
            from types import SimpleNamespace
            legacy_line = SimpleNamespace(text=text, words=text.split(), line_box=tuple(int(v) for v in n["bbox"]), word_boxes=[])
            try:
                boxes = boxer.boxes(gray, legacy_line)
                if len(boxes) != len(legacy_line.words):
                    raise ValueError("word-count mismatch")
                words = []
                for wi, (t, b) in enumerate(zip(legacy_line.words, boxes), 1):
                    # Existing ink boxers use inclusive right/bottom pixel bounds.
                    x0,y0,x1,y1 = [float(v) for v in b]
                    words.append({"id": f"{n['id']}_W{wi:04d}", "kind": "word", "parent": n["id"],
                                  "page": "P1", "bbox": [x0,y0,x1+1,y1+1], "text": t, "status": "automatic"})
                candidate = dict(d, nodes=d["nodes"]+words)
                validate(candidate)
                d["nodes"].extend(words)
                n["needs_alignment"] = False; n["status"] = "automatic"
            except Exception as error:
                n["status"] = "rejected"; n.setdefault("issues", []).append("alignment_failure:"+type(error).__name__)
                d["events"].append({"action": "alignment_failure", "line": n["id"], "error": str(error)})
    d["events"].append({"action": "production", "seconds": time.monotonic()-start,
                        "selected_lines": len(lines), "detected_lines": len(all_lines),
                        "boxer": getattr(boxer, "name", "unknown")})
    out = Path(output)
    summary = export_package(d, out)
    (out/"page.alto.xml").write_bytes((out/"P1.alto.xml").read_bytes())
    preview = pil.copy(); draw = ImageDraw.Draw(preview)
    for n in all_lines:
        draw.rectangle(n["bbox"], outline="red" if n["status"] in {"rejected", "pending", "ambiguous"} else "blue", width=2)
    preview.save(out/"overlay.jpg")
    (out/"transcription.txt").write_text("\n".join(n["id"]+"\t"+n.get("text", "") for n in all_lines), encoding="utf-8")
    summary.update({"reader_calls": len(batches), "selected_lines": len(lines),
                    "lignes_detectees": len(all_lines),
                    "lignes_retenues": sum(not n["needs_alignment"] for n in all_lines),
                    "lignes_ecartees": sum(n["status"] == "rejected" for n in all_lines)})
    (out/"provenance.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if verbose:
        print(json.dumps(summary, ensure_ascii=False))
    return summary
