"""Freeze one blind semantic pass after development-only convention audit."""
from pathlib import Path
import hashlib
import json
import random

import cv2
import numpy as np
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
PAGE = "0015"
SEED = "bbvlm-semantic-v1-2026092705"
OUT = ROOT / "experiments/loop/spiritualist-v1/semantic-v1-validation"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
TOKENS = [a + b for a in "ABCDEFGHJKLMNPQRSTUVWXYZ" for b in "23456789"]


def polygon(block):
    shape = block.find("a:Shape/a:Polygon", NS)
    if shape is not None:
        return np.array([[int(float(v)) for v in p.split(",")] for p in shape.get("POINTS").split()], np.int32)
    x, y = int(block.get("HPOS")), int(block.get("VPOS"))
    w, h = int(block.get("WIDTH")), int(block.get("HEIGHT"))
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], np.int32)


def stable_id(source_id):
    return "R" + hashlib.sha256(f"spiritualist|{PAGE}|{source_id}".encode()).hexdigest()[:16]


def main():
    conventions = json.loads((ROOT / "experiments/loop/spiritualist-v1/semantic-v1/development-conventions.json").read_text())
    if conventions["pages"] != ["0009", "0038", "0041", "0043"] or conventions["violations"]:
        raise ValueError("development convention audit is missing or inconsistent")
    input_dir, eval_dir = OUT / "input", OUT / "evaluation"
    input_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)
    xml = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{PAGE}_*.xml"))
    tree = E.parse(str(xml)); page_node = tree.find(".//a:Page", NS)
    blocks = tree.findall(".//a:TextBlock", NS)
    image_path = ROOT / f"corpora/spiritualist/companion/Spiritualist_Images/{PAGE}.png"
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(image_path)
    overlay = image.copy()
    token_pool = TOKENS.copy(); random.Random(SEED).shuffle(token_pool)
    binding, rows = {}, []
    for block, token in zip(blocks, token_pool):
        source_id = block.get("ID"); rid = stable_id(source_id); binding[token] = rid
        pts = polygon(block)
        colour = tuple(int(40 + v % 196) for v in hashlib.sha256(token.encode()).digest()[:3])
        cv2.polylines(overlay, [pts], True, colour, 8, cv2.LINE_AA)
        x, y = int(pts[:, 0].min()), int(pts[:, 1].min())
        cv2.rectangle(overlay, (x, max(0, y - 66)), (x + 145, y + 5), (255, 255, 255), -1)
        cv2.putText(overlay, token, (x + 6, max(48, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.7, colour, 5, cv2.LINE_AA)
        bx, by = float(block.get("HPOS")), float(block.get("VPOS"))
        bw, bh = float(block.get("WIDTH")), float(block.get("HEIGHT"))
        rows.append({
            "id": rid, "source_id": source_id, "bbox": [bx, by, bx + bw, by + bh],
            "reading_order": int(block.get("READING_ORDER")),
            "semantic_unit": block.get("SSU_ID"), "role": block.get("BLOCK_TYPE"),
        })
    original_name, overlay_name = f"{PAGE}-original.png", f"{PAGE}-regions.png"
    cv2.imwrite(str(input_dir / original_name), image)
    cv2.imwrite(str(input_dir / overlay_name), overlay)
    gates = {
        "raw_structural_valid": True,
        "eligibility_precision_min": 0.90,
        "eligibility_recall_min": 0.90,
        "role_accuracy_min": 0.80,
        "semantic_group_pair_f1_min": 0.80,
        "combined_order_pair_recall_min": 0.95,
    }
    request = {
        "schema": "bbvlm.blind-semantic-request/1", "page": PAGE, "passes": 1,
        "allowed_tokens": sorted(binding), "images": [original_name, overlay_name],
        "instruction": (
            "Inspect the original and labelled image. The CPU already computes physical reading order, so do not return an order. "
            "In one pass: (1) assign every token exactly one role from MASTHEAD, HEADER, TEXT, ADVERT, OTHER, UNKNOWN; "
            "(2) list the tokens eligible for the main reading stream; (3) partition every token exactly once into semantic units. "
            "Development-only corpus conventions: MASTHEAD and OTHER are excluded; HEADER and TEXT are included; a HEADER normally "
            "shares a unit with its following TEXT when they form one item; units observed in development do not cross columns; masthead "
            "fragments share one MASTHEAD unit; unrelated notices or adverts stay separate. These are provisional conventions, so mark "
            "uncertainty rather than forcing a confident semantic interpretation. Tokens are random and opaque. Return JSON only."
        ),
        "response_schema": {
            "schema": "bbvlm.blind-semantic-response/1", "page": PAGE,
            "eligible_tokens": ["short token"],
            "groups": [{"id": "G1", "tokens": ["short token"], "kind": "ARTICLE|NOTICE|ADVERT|MASTHEAD|OTHER|UNKNOWN", "label": "neutral description", "uncertain": False}],
            "roles": {"short token": "MASTHEAD|HEADER|TEXT|ADVERT|OTHER|UNKNOWN"},
            "uncertain_tokens": [], "notes": "short string",
        },
        "leakage_control": "Random visual tokens reveal no source ID, order, role or semantic unit. Validation labels and XML are outside the reader packet.",
        "binding_control": "Strict software validation binds tokens after response; no repair is permitted.",
        "frozen_gates": gates,
        "reference_warning": "Distributed role/order/SSU fields are provisional labels, not independently adjudicated truth. Page 0015 is consumed after scoring.",
    }
    reference = {
        "schema": "bbvlm.blind-semantic-reference/1", "page": PAGE,
        "page_bbox": [0, 0, float(page_node.get("WIDTH")), float(page_node.get("HEIGHT"))],
        "regions": rows,
    }
    secret = {"schema": "bbvlm.visual-token-binding/1", "page": PAGE, "token_to_id": binding}
    (input_dir / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (eval_dir / "reference.json").write_text(json.dumps(reference, indent=2) + "\n")
    (eval_dir / "token-binding.json").write_text(json.dumps(secret, indent=2) + "\n")
    print(json.dumps({"page": PAGE, "regions": len(rows), "input": str(input_dir), "gates": gates}, indent=2))


if __name__ == "__main__":
    main()
