#!/usr/bin/env python3
"""Render worst fixed-assignment A36 regressions for actual visual inspection."""
from pathlib import Path
import json

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/predicted-lines-a36"


def panel(image, item, box_key, color, width=360, height=120):
    boxes = [item["reference"], item[box_key]]
    x0 = max(0, int(min(b[0] for b in boxes)) - 35)
    y0 = max(0, int(min(b[1] for b in boxes)) - 30)
    x1 = min(image.shape[1], int(max(b[2] for b in boxes)) + 35)
    y1 = min(image.shape[0], int(max(b[3] for b in boxes)) + 30)
    crop = image[y0:y1, x0:x1].copy()
    for key, c in (("reference", (255, 120, 0)), (box_key, color)):
        b = item[key]
        cv2.rectangle(crop, (int(b[0]) - x0, int(b[1]) - y0),
                      (int(b[2]) - x0, int(b[3]) - y0), c, 2)
    scale = min(width / max(1, crop.shape[1]), height / max(1, crop.shape[0]))
    resized = cv2.resize(crop, (max(1, int(crop.shape[1] * scale)), max(1, int(crop.shape[0] * scale))))
    canvas = np.full((height, width, 3), 255, np.uint8)
    yy, xx = (height - resized.shape[0]) // 2, (width - resized.shape[1]) // 2
    canvas[yy:yy + resized.shape[0], xx:xx + resized.shape[1]] = resized
    return canvas


def main():
    split = json.loads((EXP / "split.json").read_text())
    regressions = json.loads((EXP / "output/regressions.json").read_text())[:12]
    page_info = {p["page"]: p for p in split["pages"]}
    rows, records = [], []
    for item in regressions:
        image = cv2.imread(str(EXP / "source" / page_info[item["page"]]["image"]))
        native = panel(image, item, "native", (0, 180, 0))
        refined = panel(image, item, "refined", (0, 0, 220))
        label = np.full((38, 720, 3), 255, np.uint8)
        text = f"{item['page']} {item['reference_text']} / {item['predicted_text']}  {item['old_iou']:.3f}->{item['new_iou']:.3f}"
        cv2.putText(label, text[:100], (8, 25), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 1, cv2.LINE_AA)
        rows.append(np.vstack([label, np.hstack([native, refined])]))
        records.append({k: item[k] for k in ("page", "line", "reference_text", "predicted_text",
                                             "old_iou", "new_iou", "delta", "reference", "native", "refined")})
    cv2.imwrite(str(EXP / "output/worst-regressions.png"), np.vstack(rows))
    (EXP / "output/visual-audit-cases.json").write_text(json.dumps(records, indent=2) + "\n")
    print(EXP / "output/worst-regressions.png")


if __name__ == "__main__":
    main()
