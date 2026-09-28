#!/usr/bin/env python3
"""Open the frozen A36 files and verify their Git blob identities."""
from pathlib import Path
import hashlib, json, time, urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
EXP = BASE / "predicted-lines-a36"
SOURCE = EXP / "source"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def fsha(path):
    return sha(path.read_bytes())


def main():
    split = json.loads((EXP / "split.json").read_text())
    assert split["status"] == "frozen_unopened"
    checks = {"protocol": EXP / "PROTOCOL.md", "freeze": ROOT / "scripts/freeze_predicted_lines_a36.py",
              "open": Path(__file__), "infer": ROOT / "scripts/run_predicted_lines_a36.py",
              "evaluate": ROOT / "scripts/evaluate_predicted_lines_a36.py",
              "component_refiner": ROOT / "src/bbvlm/component_boxes.py",
              "tree": BASE / "reference-a18/source/tree.json"}
    for key, path in checks.items():
        assert fsha(path) == split["sealed_sha256"][key], f"sealed file changed: {key}"
    files = []
    for page in split["pages"]:
        for kind in ("xml", "image"):
            rel = page[kind]
            url = f"https://raw.githubusercontent.com/OCR-D/OCR-D-GT-VD-SBB/{split['revision']}/{rel}"
            with urllib.request.urlopen(url, timeout=180) as response:
                data = response.read()
            assert blob(data) == page[kind + "_blob"]
            dest = SOURCE / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            files.append({"kind": kind, "path": rel, "bytes": len(data),
                          "git_blob": blob(data), "sha256": sha(data)})
    out = {"schema": "bbvlm.predicted-lines-a36-opened/1", "status": "opened_verified",
           "opened_unix": time.time(), "split_sha256": fsha(EXP / "split.json"), "files": files}
    (EXP / "opened.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
