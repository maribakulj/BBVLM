"""Run the frozen A72 Eynollah textline diagnostic with native SavedModel.

The ONNX Runtime backend was rejected before inference because it attempted
unneeded external telemetry.  This runner uses the matching public Eynollah
SavedModel locally and preserves the already-frozen image and scoring protocol.
"""
import hashlib
import json
import math
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "4")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")

import cv2
import numpy as np
import tensorflow as tf

from evaluate_crop_geometry_a65 import ROOT, polygon

OUT = ROOT / "experiments/loop/next-a72"
MODEL = ROOT / "models/eynollah/native/modelens_textline_0_1__2_4_16092024"
MODEL_HASHES = {
    "config.json": "aac06e8f74e82812db2d2534034a434bfb162a0022d62d6815a92cf4c7ac9585",
    "fingerprint.pb": "e1757519fac1208e1f2c6625a79e433762d57db48d399db69a1466f2cf560e46",
    "keras_metadata.pb": "3c3f53339a7f5b7db6c3407ded7ccaa32a3cdf165ee801d332fa7f704d333ca2",
    "saved_model.pb": "9b799e2510b5b144a7b94328b7e3b49b45edb1a74ec5e1f27473d6ad1a993825",
    "variables/variables.data-00000-of-00001": "5da57fd65ecbdaf49657318740121600583de9b57774b96a854dc8957e9d8a15",
    "variables/variables.index": "aeb2d2d226f27e26de38eb40ab4599b12e2b5fec89dacc290cc2b625631f1b5b",
}
PAGES = ["Reichs_Post_Reuter_1700-11-16_0001", "Koelnische_Zeitung_1924_0001"]
TARGET_WIDTH = 2000
PATCH = 672
MARGIN = 67


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_model() -> None:
    present = {p.relative_to(MODEL).as_posix() for p in MODEL.rglob("*") if p.is_file()}
    assert present == set(MODEL_HASHES), (present, set(MODEL_HASHES))
    for rel, digest in MODEL_HASHES.items():
        assert sha(MODEL / rel) == digest, rel


def parse_xml(name, expected):
    path = ROOT / "corpora/chronicling-germany/annotations" / f"{name}.xml"
    assert sha(path) == expected[path.name]
    root = ET.fromstring(path.read_bytes())
    ns = {"p": root.tag.split("}")[0][1:]}
    page = root.find("p:Page", ns)
    lines = []
    for region in page.findall("p:TextRegion", ns):
        for element in region.findall("p:TextLine", ns):
            shape = polygon(element, ns)
            if shape is not None:
                lines.append((element.get("id"), shape))
    return lines, sha(path)


def load_predictor():
    model = tf.saved_model.load(str(MODEL))
    signature = model.signatures["serving_default"]
    inputs = signature.structured_input_signature[1]
    outputs = signature.structured_outputs
    assert list(inputs) == ["input_1"]
    assert inputs["input_1"].shape.as_list() == [None, PATCH, PATCH, 3]
    assert inputs["input_1"].dtype == tf.float32
    assert len(outputs) == 1
    output_name = next(iter(outputs))

    def predict(batch):
        result = signature(input_1=tf.convert_to_tensor(batch, dtype=tf.float32))
        return result[output_name].numpy()

    return predict, output_name


def predict_tiled(predict, image):
    """Mirror Eynollah 0.9.2 overlapping-patch accumulation."""
    height, width = image.shape[:2]
    mid = PATCH - 2 * MARGIN
    nxf = math.ceil((width - 2.0 * MARGIN) / mid)
    nyf = math.ceil((height - 2.0 * MARGIN) / mid)
    window = 1 / (1 + np.exp(5.0 - 5 * np.arange(2 * MARGIN) / MARGIN))
    prediction = np.zeros((height, width, 3), dtype=np.float32)
    tiles = 0
    for i in range(nxf):
        for j in range(nyf):
            xd, yd = i * mid, j * mid
            xu, yu = xd + PATCH, yd + PATCH
            xs = max(0, xu - width)
            ys = max(0, yu - height)
            if xs:
                xu, xd = width, width - PATCH
            if ys:
                yu, yd = height, height - PATCH
            tile = image[yd:yu, xd:xu].astype(np.float32) / 255.0
            assert tile.shape == (PATCH, PATCH, 3)
            probs = predict(tile[np.newaxis])[0]
            ay = np.ones(PATCH - ys, dtype=np.float32)
            ax = np.ones(PATCH - xs, dtype=np.float32)
            if MARGIN and j > 0:
                ay[: 2 * MARGIN] = window
            if MARGIN and j < nyf - 1:
                ay[-2 * MARGIN :] = 1 - window
            if MARGIN and i > 0:
                ax[: 2 * MARGIN] = window
            if MARGIN and i < nxf - 1:
                ax[-2 * MARGIN :] = 1 - window
            part = probs[ys:, xs:] * ay[:, None, None] * ax[None, :, None]
            prediction[yd + ys : yu, xd + xs : xu] += part
            tiles += 1
    return np.argmax(prediction, axis=2).astype(np.uint8) == 1, tiles


def polygon_coverage(mask, geom, sx, sy):
    pts = np.rint(np.asarray(geom.exterior.coords) * np.array([sx, sy])).astype(np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(mask.shape[1], x + w), min(mask.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    local = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(local, [pts - np.array([x0, y0])], 1)
    denom = int(local.sum())
    return float(np.logical_and(local, mask[y0:y1, x0:x1]).sum() / denom) if denom else 0.0


def main():
    started = time.perf_counter()
    verify_model()
    assets = json.loads((ROOT / "experiments/loop/next-a69/assets.json").read_text())["images"]
    asset = {row["page"]: row for row in assets}
    a70 = json.loads((ROOT / "experiments/loop/next-a70/report-v2.json").read_text())
    zero = {(row["page"], row["line_id"]) for row in a70["rows"] if not row["contributors"]}
    predict, output_name = load_predictor()
    masks, image_audit = {}, {}
    for page in PAGES:
        path = ROOT / asset[page]["path"]
        assert sha(path) == asset[page]["sha256"]
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        assert image is not None
        h, w = image.shape[:2]
        nh = round(h * TARGET_WIDTH / w)
        resized = cv2.resize(image, (TARGET_WIDTH, nh), interpolation=cv2.INTER_AREA)
        tick = time.perf_counter()
        mask, tiles = predict_tiled(predict, resized)
        elapsed = time.perf_counter() - tick
        out = OUT / f"{page}-textline-mask.png"
        assert cv2.imwrite(str(out), mask.astype(np.uint8) * 255)
        masks[page] = (mask, TARGET_WIDTH / w, nh / h)
        image_audit[page] = {
            "image_sha256": sha(path), "shape": [h, w], "resized_shape": [nh, TARGET_WIDTH],
            "mask_sha256": sha(out), "tiles": tiles, "seconds": elapsed,
            "positive_pixels": int(mask.sum()),
        }
    expected = {row["file"]: row["sha256"] for row in json.loads(
        (ROOT / "experiments/loop/chronicling-a58/audit.json").read_text())["files_detail"]}
    rows = []
    for page in PAGES:
        lines, xml_hash = parse_xml(page, expected)
        mask, sx, sy = masks[page]
        for line_id, geom in lines:
            coverage = polygon_coverage(mask, geom, sx, sy)
            rows.append({"page": page, "line_id": line_id, "coverage": coverage,
                         "hit_ge1pct": coverage >= 0.01,
                         "a70_zero_contributor": (page, line_id) in zero,
                         "xml_sha256": xml_hash})
    target = [row for row in rows if row["a70_zero_contributor"]]
    target_hits = sum(row["hit_ge1pct"] for row in target)
    ratio = target_hits / len(target) if target else 0.0
    report = {
        "status": "consumed_textline_stage_diagnostic",
        "implementation": "Eynollah 0.9.2 native textline SavedModel only",
        "backend": "tensorflow-cpu 2.16.2 tf.saved_model.load",
        "model_file_sha256": MODEL_HASHES,
        "signature_output": output_name,
        "pages": PAGES, "image_audit": image_audit,
        "all_lines": len(rows), "all_lines_hit_ge1pct": sum(row["hit_ge1pct"] for row in rows),
        "zero_contributor_lines": len(target), "zero_contributor_hit_ge1pct": target_hits,
        "zero_contributor_hit_ratio": ratio, "local_gate_ge50pct": ratio >= 0.5,
        "rows": rows, "detector_forwards": sum(row["tiles"] for row in image_audit.values()),
        "vlm_calls": 0, "ocr_calls": 0, "test_pages_opened": 0,
        "seconds": time.perf_counter() - started, "all_scientific_gates_passed": False,
        "limitations": ["Consumed pages and oracle-selected residuals.",
                        "A 1% mask hit is line recall, not an ALTO box.",
                        "PAGE line polygons and a single threshold are not perfect truth."],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    keys = ("all_lines", "all_lines_hit_ge1pct", "zero_contributor_lines",
            "zero_contributor_hit_ge1pct", "zero_contributor_hit_ratio",
            "local_gate_ge50pct", "detector_forwards", "seconds")
    print(json.dumps({key: report[key] for key in keys}, indent=2))


if __name__ == "__main__":
    main()
