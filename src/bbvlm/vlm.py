"""Provider-independent, image-grounded batches and recorded response replay."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
from .document import index, digest, validate

PROMPT = """Read the attached image crops. Return JSON keyed by the exact requested line IDs.
Transcribe literally: preserve spelling, punctuation, long s, end-of-line hyphens,
and printed ligatures according to the specified convention. Never join lines.
Use empty text and uncertain=true if unreadable. Do not invent word coordinates.
Also propose region roles, region reading-order edges, article groups, and visible
metadata with evidence IDs. Distinguish observed facts from interpretations.
No automatic answer is human-verified. Do not omit requested lines.
Response: {requested_line_ids: [...], lines: [{id,text,uncertain,notes}],
regions: [{id,role}], reading_order: [{before,after}],
articles: [{id,title,regions}], metadata: [{field,value,category,evidence}]}.
"""


def prepare_batch(document, image_path, page_id, line_ids, directory, *, show_ocr=False,
                  convention="diplomatic; preserve ſ and ⸗; do not modernise spelling"):
    validate(document)
    ix = index(document)
    page = ix[page_id]
    if page["kind"] != "page" or len(line_ids) != len(set(line_ids)) or not line_ids:
        raise ValueError("invalid page or empty/duplicate batch")
    for lid in line_ids:
        if lid not in ix or ix[lid]["kind"] != "line" or ix[lid]["page"] != page_id:
            raise ValueError("batch contains unknown lines or mixes pages")
    im = Image.open(image_path).convert("RGB")
    if [im.width, im.height] != page["bbox"][2:]:
        raise ValueError("source image dimensions differ from the graph")
    out = Path(directory); out.mkdir(parents=True, exist_ok=True)
    request = {"schema_version": "bbvlm.vlm-request/1", "page_id": page_id,
               "requested_line_ids": list(line_ids), "mode": "ocr_correction" if show_ocr else "blind",
               "image_sha256": hashlib.sha256(Path(image_path).read_bytes()).hexdigest(),
               "convention": convention, "prompt": PROMPT, "lines": [],
               "regions": [{"id": n["id"], "bbox": n["bbox"]} for n in document["nodes"]
                           if n["kind"] == "region" and n["page"] == page_id]}
    for lid in line_ids:
        n = ix[lid]; box = n["bbox"]
        crop_name = lid+".png"
        im.crop(tuple(box)).save(out/crop_name)
        item = {"id": lid, "region": n["parent"], "bbox": box, "image": crop_name}
        if show_ocr:
            item["ocr_text"] = n.get("text", "")
        request["lines"].append(item)
    im.save(out/"page.png")
    context = im.copy(); draw = ImageDraw.Draw(context)
    for r in request["regions"]:
        draw.rectangle(r["bbox"], outline="red", width=2)
        draw.text((r["bbox"][0], r["bbox"][1]), r["id"], fill="blue", stroke_width=1, stroke_fill="white")
    context.save(out/"regions.png")
    request["request_sha256"] = digest(request)
    (out/"request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return request
