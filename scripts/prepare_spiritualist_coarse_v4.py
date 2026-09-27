"""Freeze a blind coarse-physical/editorial packet for validation page 0044."""
from pathlib import Path
import hashlib, json, random

import cv2
import numpy as np
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
PAGE="0044";SEED="bbvlm-semantic-v4-coarse-2026092708"
OUT=ROOT/"experiments/loop/spiritualist-v1/semantic-v4-coarse-validation"
PROFILE=ROOT/"experiments/loop/spiritualist-v1/semantic-v4-coarse/profile.json"
NS={"a":"http://www.loc.gov/standards/alto/ns-v4#"}
TOKENS=[a+b for a in "ABCDEFGHJKLMNPQRSTUVWXYZ" for b in "23456789"]


def polygon(block):
    shape=block.find("a:Shape/a:Polygon",NS)
    if shape is not None:
        return np.array([[int(float(v)) for v in p.split(",")] for p in shape.get("POINTS").split()],np.int32)
    x,y=int(block.get("HPOS")),int(block.get("VPOS"));w,h=int(block.get("WIDTH")),int(block.get("HEIGHT"))
    return np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h]],np.int32)


def stable_id(source_id):
    return "R"+hashlib.sha256(f"spiritualist|{PAGE}|{source_id}".encode()).hexdigest()[:16]


def main():
    profile=json.loads(PROFILE.read_text())
    if profile["validation_page"]!=PAGE or profile["frozen_before_validation"]!="2026-09-27":
        raise ValueError("frozen coarse profile missing")
    config=json.loads((ROOT/"experiments/loop/spiritualist-v1/semantic-v4-coarse/config.json").read_text())
    if config["max_header_height_page_ratio"]!=profile["height_config"]["max_header_height_page_ratio"]:
        raise ValueError("frozen height profile does not match development calibration")
    input_dir,eval_dir=OUT/"input",OUT/"evaluation";input_dir.mkdir(parents=True,exist_ok=True);eval_dir.mkdir(parents=True,exist_ok=True)
    xml=next((ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{PAGE}_*.xml"))
    tree=E.parse(str(xml));page_node=tree.find(".//a:Page",NS);blocks=tree.findall(".//a:TextBlock",NS)
    image_path=ROOT/f"corpora/spiritualist/companion/Spiritualist_Images/{PAGE}.png";image=cv2.imread(str(image_path))
    if image is None:raise FileNotFoundError(image_path)
    overlay=image.copy();pool=TOKENS.copy();random.Random(SEED).shuffle(pool);binding={};rows=[]
    for block,token in zip(blocks,pool):
        source_id=block.get("ID");rid=stable_id(source_id);binding[token]=rid;pts=polygon(block)
        colour=tuple(int(40+v%196) for v in hashlib.sha256(token.encode()).digest()[:3])
        cv2.polylines(overlay,[pts],True,colour,8,cv2.LINE_AA);x,y=int(pts[:,0].min()),int(pts[:,1].min())
        cv2.rectangle(overlay,(x,max(0,y-66)),(x+145,y+5),(255,255,255),-1)
        cv2.putText(overlay,token,(x+6,max(48,y-10)),cv2.FONT_HERSHEY_SIMPLEX,1.7,colour,5,cv2.LINE_AA)
        bx,by=float(block.get("HPOS")),float(block.get("VPOS"));bw,bh=float(block.get("WIDTH")),float(block.get("HEIGHT"))
        rows.append({"id":rid,"source_id":source_id,"bbox":[bx,by,bx+bw,by+bh],
                     "reading_order":int(block.get("READING_ORDER")),"semantic_unit":block.get("SSU_ID"),
                     "physical_role":block.get("BLOCK_TYPE")})
    scale=1200/image.shape[1];size=(1200,round(image.shape[0]*scale))
    original=cv2.resize(image,size,interpolation=cv2.INTER_AREA);labelled=cv2.resize(overlay,size,interpolation=cv2.INTER_AREA)
    original_name=f"{PAGE}-original-reader.jpg";overlay_name=f"{PAGE}-regions-reader.jpg"
    cv2.imwrite(str(input_dir/original_name),original,[cv2.IMWRITE_JPEG_QUALITY,90])
    cv2.imwrite(str(input_dir/overlay_name),labelled,[cv2.IMWRITE_JPEG_QUALITY,90])
    request={
      "schema":"bbvlm.blind-coarse-faceted-request/1","page":PAGE,"passes":1,"allowed_tokens":sorted(binding),
      "images":[original_name,overlay_name],
      "instruction":(
        "Inspect both images. For every opaque token, return two independent labels. coarse_roles describes visible/source layout: "
        "STREAM for every ordinary readable heading or body block, including advertisements and notices; MASTHEAD only for page-title/date/page-number fragments; "
        "OTHER for ornaments/non-reading elements; UNKNOWN if genuinely unreadable. Do not distinguish HEADER from TEXT: frozen software does that from geometry. "
        "editorial_genres describes function: ARTICLE, ADVERT, NOTICE, MASTHEAD, OTHER, or UNKNOWN. Genre never controls STREAM membership. "
        "Do not return eligibility, order, groups, articles, transcription, or fine physical roles. Mark uncertainty separately for each axis. Tokens are random. Return JSON only."),
      "response_schema":{"schema":"bbvlm.blind-coarse-faceted-response/1","page":PAGE,
        "coarse_roles":{"short token":"STREAM|MASTHEAD|OTHER|UNKNOWN"},
        "editorial_genres":{"short token":"ARTICLE|ADVERT|NOTICE|MASTHEAD|OTHER|UNKNOWN"},
        "uncertain_coarse_tokens":[],"uncertain_genre_tokens":[],"notes":"short string"},
      "frozen_profile":profile,
      "leakage_control":"Random tokens reveal no source ID, order, physical role, genre or semantic unit. XML, binding and reference are outside the reader packet.",
      "binding_control":"Strict software validation binds both complete maps; no repair is permitted.",
      "reference_warning":f"Physical role/order/SSU are provisional corpus labels. Editorial genre has no adjudicated reference and is not scored. Page {PAGE} is consumed after scoring."
    }
    reference={"schema":"bbvlm.blind-coarse-faceted-reference/1","page":PAGE,
      "page_bbox":[0,0,float(page_node.get("WIDTH")),float(page_node.get("HEIGHT"))],"regions":rows}
    secret={"schema":"bbvlm.visual-token-binding/1","page":PAGE,"token_to_id":binding}
    (input_dir/"request.json").write_text(json.dumps(request,indent=2)+"\n")
    (eval_dir/"reference.json").write_text(json.dumps(reference,indent=2)+"\n")
    (eval_dir/"token-binding.json").write_text(json.dumps(secret,indent=2)+"\n")
    print(json.dumps({"page":PAGE,"regions":len(rows),"reader_size":size,"input":str(input_dir),"gates":profile["frozen_gates"]},indent=2))


if __name__=="__main__":main()
