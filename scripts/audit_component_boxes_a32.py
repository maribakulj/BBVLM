"""Render unmarked pixels and retained ink for six largest A32 regressions."""
import json
from PIL import Image, ImageDraw
import cv2
import numpy as np
import evaluate_component_boxes_a32 as run
from bbvlm.component_boxes import selected_ink


def main():
    split = json.loads((run.SOURCE / "split.json").read_text())
    run.core.SOURCE = run.SOURCE / "source"
    rows, paths = run.core.load_rows(split)
    lookup = {r["id"]: r for r in rows}
    cases = json.loads((run.OUT / "extremes.json").read_text())[:6]
    canvas = Image.new("RGB", (1200, 6*230), "white")
    draw = ImageDraw.Draw(canvas)
    for index, case in enumerate(cases):
        row = lookup[case["line"]]
        gray = cv2.imread(str(paths[row["page"]]), cv2.IMREAD_GRAYSCALE)
        lx, ly, rx, ry = row["line_bbox"]
        crop = gray[ly:ry, lx:rx]
        _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        mask, diag = selected_ink(ink, "satellites")
        coords = np.asarray([case[k] for k in ("reference", "raw", "candidate")])
        x0 = max(lx, int(coords[:, 0].min())-5); x1 = min(rx, int(coords[:, 2].max())+5)
        scale = min(3, 380/max(1, x1-x0), 185/max(1, ry-ly))
        inputs = [crop[:, x0-lx:x1-lx], 255-ink[:, x0-lx:x1-lx], (255*(~mask[:, x0-lx:x1-lx])).astype("uint8")]
        draw.text((5,index*230+3), f'{case["line"]} token {case["word_index"]}: {case["text"]}  IoU {case["old_iou"]:.3f} -> {case["new_iou"]:.3f}', fill="black")
        for j,(title,arr) in enumerate(zip(["original / no overlay", "raw Otsu", "kept ink / satellites"], inputs)):
            draw.text((j*400+5,index*230+20),title,fill="black")
            im=Image.fromarray(arr).resize((max(1,round(arr.shape[1]*scale)),max(1,round(arr.shape[0]*scale))))
            canvas.paste(im,(j*400+5,index*230+40))
    canvas.save(run.OUT / "regressions-clean.png")


if __name__ == "__main__":
    main()
