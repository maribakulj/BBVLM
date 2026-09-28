"""Fetch exactly the frozen A76 public page images with upstream verification."""
import concurrent.futures
import json

from fetch_crop_pilot_a66 import ROOT, REV, fetch

OUT = ROOT / "experiments/loop/next-a76"


def main():
    split = json.loads((OUT / "split.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(fetch, split["pages"]))
    payload = {"revision": REV, "images": rows, "test_pages_opened": 0}
    (OUT / "assets.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"verified_images": len(rows), "bytes": sum(row["bytes"] for row in rows)}))


if __name__ == "__main__":
    main()
