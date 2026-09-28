"""Freeze four new time-stratified Training pages for A76."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/next-a76"
STRATA = [(1600, 1749), (1750, 1849), (1850, 1900), (1901, 1945)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(name):
    return hashlib.sha256(("A76-v1:" + name).encode()).hexdigest()


def main():
    split_path = ROOT / "experiments/loop/chronicling-a58/official_split.json"
    split = json.loads(split_path.read_text())
    excluded = set(json.loads((ROOT / "experiments/loop/next-a69/split.json").read_text())["pages"])
    excluded.update(json.loads((ROOT / "experiments/loop/next-a74/split.json").read_text())["pages"])
    selected, audit = [], []
    for low, high in STRATA:
        eligible = []
        for name in split["Training"]:
            match = re.search(r"(1[6-9]\d{2})", name)
            if match and low <= int(match.group(1)) <= high and name not in excluded:
                eligible.append(name)
        assert eligible
        choice = min(eligible, key=rank)
        selected.append(choice)
        audit.append({"range": [low, high], "eligible": len(eligible),
                      "selected": choice, "selection_sha256": rank(choice)})
    assert len(set(selected)) == 4
    assert set(selected) <= set(split["Training"])
    assert not set(selected) & set(split["Validation"])
    assert not set(selected) & set(split["Test"])
    assert not set(selected) & excluded
    protocol = OUT / "PROTOCOL.md"
    payload = {
        "schema": "bbvlm.a76.split/1", "status": "frozen_unopened_for_a76",
        "pages": selected, "strata": audit, "official_split": "Training",
        "official_split_sha256": sha(split_path), "protocol_sha256": sha(protocol),
        "excluded_pages": sorted(excluded),
        "selection_rule": "minimum sha256(A76-v1:<id>) in each year stratum",
        "test_pages_opened": 0,
    }
    (OUT / "split.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"pages": selected, "excluded": len(excluded), "test_pages_opened": 0}, indent=2))


if __name__ == "__main__":
    main()
