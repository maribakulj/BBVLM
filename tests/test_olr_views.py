import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from olr_views import write_native_views


def test_native_views_cover_large_regions_and_preserve_every_source_pixel(tmp_path):
    rng=np.random.default_rng(4);pixels=rng.integers(0,255,(220,350,3),dtype=np.uint8)
    image=tmp_path/'image.png';Image.fromarray(pixels).save(image)
    annotations=[dict(id='L1',bbox=[20,20,330,200])]
    geometry=[dict(id='G_0001',bbox=[20,20,330,200],line_ids=['L1'])]
    regions=[dict(id='S_1',bbox=[1.1,1.3,348.6,3.2])]
    result=write_native_views(image,annotations,geometry,regions,tmp_path/'views',limit=128,overlap=16)
    covered=np.zeros(pixels.shape[:2],bool)
    for view in result['views']:
        x0,y0,x1,y1=view['source_box'];x,y=view['paste_origin'];native=np.asarray(Image.open(view['path']))
        assert np.array_equal(native[y:y+y1-y0,x:x+x1-x0],pixels[y0:y1,x0:x1])
        assert view['pixel_scale']==1 and view['source_pixels']
        if view['id']=='G_0001':covered[y0:y1,x0:x1]=True
    assert covered[20:200,20:330].all()
    assert result['geometry_unchanged'] and result['criteria_met'] is False


def test_native_views_refuse_missing_or_duplicate_line_coverage(tmp_path):
    import pytest
    image=tmp_path/'image.png';Image.new('RGB',(100,100),'white').save(image)
    annotations=[dict(id='L1',bbox=[10,10,90,90])]
    with pytest.raises(ValueError,match='couvrir'):
        write_native_views(image,annotations,[],[],tmp_path/'missing')
    group=dict(id='G1',bbox=[10,10,90,90],line_ids=['L1','L1'])
    with pytest.raises(ValueError,match='couvrir'):
        write_native_views(image,annotations,[group],[],tmp_path/'duplicate')
