"""Oracle-selected audit views; no reference text sent to the reader."""
import hashlib,json,math,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a63';B=P/'blind';B.mkdir(exist_ok=True)
source=ROOT/'experiments/loop/bnl-independent-a54/source/0455.png'
xml=ROOT/'experiments/loop/bnl-independent-a54/source/0455.xml'
im=Image.open(source);ns={'a':'http://www.loc.gov/standards/alto/ns-v4#'}
lines=ET.parse(xml).getroot().findall('.//a:TextLine',ns)
selection=[('R729',26),('R184',24),('R563',64),('R902',20),('R347',63),('R816',22)]
items=[];mapping=[]
for key,index in selection:
 line=lines[index];top=math.floor(float(line.attrib['VPOS'])*300/254)-8
 bottom=math.ceil((float(line.attrib['VPOS'])+float(line.attrib['HEIGHT']))*300/254)+8
 box=(0,max(0,top),im.width,min(im.height,bottom));crop=im.crop(box)
 native=B/(key+'.png');large=B/(key+'-zoom.png');crop.save(native)
 crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST).save(large)
 items.append({'id':key,'images':[str(native.relative_to(ROOT)),str(large.relative_to(ROOT))],
 'sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in [native,large]]})
 mapping.append({'id':key,'line_index':index,'box':box})
request={'task':'Inspect both images for every item using view_image at original detail. They show the same printed line at native scale and integer pixel replication. Transcribe that line faithfully, including historical spelling and accents; never modernize or correct implausible words. Do not reconstruct missing detail. Report ambiguous spans and visible stroke/diacritic evidence separately. Read only this request and its images; no other files, earlier outputs, references, scores or agents. Return exactly the requested opaque IDs and the actual list of inspected image paths.',
'items':items,'output_schema':{'items':[{'id':'opaque ID','text':'literal full line','uncertain_spans':[{'text':'span','reason':'visible reason'}]}],'inspected_images':['relative input paths']}}
(B/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
(P/'private-map.json').write_text(json.dumps({'selection':'oracle_consumed_diagnostic','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'xml_sha256':hashlib.sha256(xml.read_bytes()).hexdigest(),'mapping':mapping},indent=2)+'\n')
