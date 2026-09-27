"""Freeze a filename-only A10 split from pages untouched by the initial split."""
from pathlib import Path
import json,random

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/loop/spiritualist-v1/semantic-v6-typography"
OLD_DEV={"0009","0038","0041","0043"}
OLD_VAL={"0003","0008","0014","0015","0029","0039","0044","0050"}
SEED=2026092710

def main():
    pages=sorted(p.name.split("_",1)[0] for p in (ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob("*.xml"))
    remaining=[p for p in pages if p not in OLD_DEV|OLD_VAL]
    rng=random.Random(SEED);rng.shuffle(remaining)
    split={"schema":"bbvlm.semantic-v6-split/1","seed":SEED,
      "selection":"page filenames only; no image, text, role, order or difficulty inspected",
      "development_pages":sorted(remaining[:8]),"validation_pages":sorted(remaining[8:16]),
      "reserve_pages":sorted(remaining[16:]),"excluded_consumed_pages":sorted(OLD_DEV|OLD_VAL),
      "purpose":"develop and independently validate internal-typography HEADER/TEXT classification plus coarse VLM/order",
      "warning":"Distributed roles and SSU remain provisional; no page can validate word geometry."}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"split.json").write_text(json.dumps(split,indent=2)+"\n")
    print(json.dumps(split,indent=2))

if __name__=="__main__":main()
