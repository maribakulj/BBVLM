#!/usr/bin/env python3
"""Open the pre-registered A25 holdout and verify pinned Git blobs."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "loop" / "french-holdout-a25"
SPLIT = EXP / "split.json"
PROTOCOL = EXP / "PROTOCOL.md"
SOURCE = EXP / "source"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> None:
    split_bytes = SPLIT.read_bytes()
    split = json.loads(split_bytes)
    if split.get("status") != "frozen_unopened":
        raise SystemExit("refusing to open: split is not frozen_unopened")
    if sha256(PROTOCOL.read_bytes()) != split["protocol_sha256"]:
        raise SystemExit("protocol changed after split freeze")

    revision = split["revision"]
    records = []
    for page in split["pages"]:
        for kind in ("xml", "image"):
            rel = page[kind]
            expected = page[f"{kind}_blob"]
            url = (
                "https://raw.githubusercontent.com/OCR-D/OCR-D-GT-VD-SBB/"
                f"{revision}/{rel}"
            )
            with urllib.request.urlopen(url, timeout=120) as response:
                data = response.read()
            actual = git_blob(data)
            if actual != expected:
                raise SystemExit(f"Git blob mismatch for {rel}: {actual} != {expected}")
            target = SOURCE / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            records.append(
                {
                    "kind": kind,
                    "path": rel,
                    "git_blob": actual,
                    "sha256": sha256(data),
                    "bytes": len(data),
                }
            )

    opened = {
        "schema": "bbvlm.french-holdout-a25-opened/1",
        "split_sha256": sha256(split_bytes),
        "protocol_sha256": split["protocol_sha256"],
        "revision": revision,
        "opened_unix": time.time(),
        "files": records,
        "status": "opened_verified",
    }
    (EXP / "opened.json").write_text(
        json.dumps(opened, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(opened, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
