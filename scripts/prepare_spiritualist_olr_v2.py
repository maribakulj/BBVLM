"""Freeze a two-page blind validation packet with short visual tokens."""
from pathlib import Path
import hashlib
import json
import random

import cv2
import numpy as np
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("0003", "0008")
SEED = "bbvlm-olr-v2-2026092703"
OUT = ROOT / "experiments/loop/spiritualist-v1/olr-v2-validation"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
TOKENS = [a + b for a in "ABCDEFGHJKLMNPQRSTUVWXYZ" for b in "23456789"]


def polygon(block):
    shape = block.find("a:Shape/a:Polygon", NS)
    if shape is not None:
        return np.array([[int(float(v)) for v in p.split(",")] for p in shape.get("POINTS").split()], np.int32)
    x, y = int(block.get("HPOS")), int(block.get("VPOS"))
    w, h = int(block.get("WIDTH")), int(block.get("HEIGHT"))
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], np.int32)


def stable_id(page, source_id):
    return "R" + hashlib.sha256(f"spiritualist|{page}|{source_id}".encode()).hexdigest()[:16]


def main():
    input_dir = OUT / "input"
    eval_dir = OUT / "evaluation"
    input_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)
    request_pages, references, bindings = [], {}, {}
    for page in PAGES:
        xml = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))
        blocks = E.parse(str(xml)).findall(".//a:TextBlock", NS)
        image_path = ROOT / f"corpora/spiritualist/companion/Spiritualist_Images/{page}.png"
        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(image_path)
        overlay = image.copy()
        token_pool = TOKENS.copy()
        random.Random(f"{SEED}|{page}").shuffle(token_pool)
        rows, binding = [], {}
        for block, token in zip(blocks, token_pool):
            source_id = block.get("ID")
            region_id = stable_id(page, source_id)
            binding[token] = region_id
            pts = polygon(block)
            colour = tuple(int(40 + v % 196) for v in hashlib.sha256(token.encode()).digest()[:3])
            cv2.polylines(overlay, [pts], True, colour, 8, cv2.LINE_AA)
            x, y = int(pts[:, 0].min()), int(pts[:, 1].min())
            cv2.rectangle(overlay, (x, max(0, y - 66)), (x + 145, y + 5), (255, 255, 255), -1)
            cv2.putText(overlay, token, (x + 6, max(48, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.7, colour, 5, cv2.LINE_AA)
            rows.append({
                "id": region_id,
                "source_id": source_id,
                "reading_order": int(block.get("READING_ORDER")),
                "semantic_unit": block.get("SSU_ID"),
                "role": block.get("BLOCK_TYPE"),
            })
        original_name = f"{page}-original.png"
        overlay_name = f"{page}-regions.png"
        cv2.imwrite(str(input_dir / original_name), image)
        cv2.imwrite(str(input_dir / overlay_name), overlay)
        request_pages.append({
            "page": page,
            "allowed_tokens": sorted(binding),
            "images": [original_name, overlay_name],
        })
        references[page] = rows
        bindings[page] = binding
    request = {
        "schema": "bbvlm.blind-olr-request/2",
        "pages": request_pages,
        "passes": 1,
        "instruction": (
            "Inspect both the original and labelled image for every page. Infer region reading order, "
            "semantic/article-like grouping, and role only from the images. Tokens are random and opaque. "
            "For each page return every allowed token exactly once in ordered_tokens and exactly once across groups. "
            "Assign every token one role from MASTHEAD, HEADER, TEXT, ADVERT, OTHER, UNKNOWN. "
            "Use uncertain_tokens and group uncertain=true instead of inventing certainty. Return JSON only."
        ),
        "response_schema": {
            "schema": "bbvlm.blind-olr-response/2",
            "pages": [{
                "page": "page ID",
                "ordered_tokens": ["short token"],
                "groups": [{"id": "G1", "tokens": ["short token"], "label": "neutral description", "uncertain": False}],
                "roles": {"short token": "controlled role"},
                "uncertain_tokens": [],
                "notes": "short string",
            }],
        },
        "leakage_control": "Short tokens are deterministically shuffled per page and reveal neither source IDs, geometry order, reading order, text, role nor semantic unit.",
        "binding_control": "The model never handles stable IDs; strict software validation binds tokens to them after the response, with no repair.",
        "frozen_gates": {
            "raw_structural_valid": True,
            "reading_order_pair_accuracy_each_page_min": 0.90,
            "semantic_group_pair_f1_each_page_min": 0.80,
            "role_accuracy_each_page_min": 0.80,
        },
        "reference_warning": "Distributed SSU/order/role labels are provisional, not independently adjudicated ground truth. These validation pages are consumed by this fixed protocol after scoring.",
    }
    reference = {"schema": "bbvlm.blind-olr-reference/2", "pages": references}
    secret_binding = {"schema": "bbvlm.visual-token-binding/1", "pages": bindings}
    (input_dir / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (eval_dir / "reference.json").write_text(json.dumps(reference, indent=2) + "\n")
    (eval_dir / "token-binding.json").write_text(json.dumps(secret_binding, indent=2) + "\n")
    print(json.dumps({"pages": PAGES, "regions": {p: len(references[p]) for p in PAGES}, "input": str(input_dir)}, indent=2))


if __name__ == "__main__":
    main()
