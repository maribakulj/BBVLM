#!/usr/bin/env python3
"""Freeze one unopened SBB work using repository metadata only."""
from pathlib import Path
import collections, hashlib, json, time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
EXP = BASE / "predicted-lines-a36"
TREE = BASE / "reference-a18/source/tree.json"
REV = "481f7235acfc1f78e88b3c2f22f551595c3f2032"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tree = json.loads(TREE.read_text())
    assert tree["sha"] == REV and not tree["truncated"]
    blobs = {x["path"]: x for x in tree["tree"] if x["type"] == "blob"}
    consumed = set()
    for split_path in BASE.glob("**/split.json"):
        try:
            split = json.loads(split_path.read_text())
        except (ValueError, OSError):
            continue
        consumed.update(p["work"] for p in split.get("pages", []) if p.get("work"))
    works = collections.defaultdict(lambda: {"xml": [], "image": []})
    for path in blobs:
        parts = path.split("/")
        if len(parts) < 4 or parts[0] != "data":
            continue
        if "/OCR-D-GT-PAGE/" in path and path.endswith(".xml"):
            works[parts[1]]["xml"].append(path)
        if "/OCR-D-IMG/" in path and path.lower().endswith(".tif"):
            works[parts[1]]["image"].append(path)
    eligible = [w for w, v in works.items()
                if w not in consumed and len(v["xml"]) == len(v["image"]) == 4]
    chosen = min(eligible, key=lambda w: hashlib.sha256(("A36-predicted-lines:" + w).encode()).hexdigest())
    pages = []
    for xp, ip in zip(sorted(works[chosen]["xml"]), sorted(works[chosen]["image"])):
        page = Path(xp).stem.replace("OCR-D-GT-PAGE_", "")
        assert page == Path(ip).stem.replace("OCR-D-IMG_", "")
        pages.append({"work": chosen, "page": page, "xml": xp, "image": ip,
                      "xml_blob": blobs[xp]["sha"], "image_blob": blobs[ip]["sha"],
                      "xml_size": blobs[xp]["size"], "image_size": blobs[ip]["size"]})
    sealed = {
        "protocol": EXP / "PROTOCOL.md",
        "freeze": Path(__file__),
        "open": ROOT / "scripts/open_predicted_lines_a36.py",
        "infer": ROOT / "scripts/run_predicted_lines_a36.py",
        "evaluate": ROOT / "scripts/evaluate_predicted_lines_a36.py",
        "component_refiner": ROOT / "src/bbvlm/component_boxes.py",
        "tree": TREE,
    }
    out = {"schema": "bbvlm.predicted-lines-a36-split/1", "status": "frozen_unopened",
           "repository": "OCR-D/OCR-D-GT-VD-SBB", "revision": REV,
           "selection": "minimum SHA-256(A36-predicted-lines:<work>) among unconsumed four-page works",
           "excluded_consumed_works": sorted(consumed), "eligible_work_count": len(eligible),
           "work": chosen, "pages": pages, "created_unix": time.time(),
           "sealed_sha256": {k: sha(v) for k, v in sealed.items()}}
    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "split.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
