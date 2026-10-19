import sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'scripts')]
from segmenter_echelle import bounded_scale


def test_bounded_network_canvas_covers_large_and_very_wide_source_images():
    from segmentation import tile_starts
    for width,height,glyph in ((7392,9664,28),(20000,200,4),(500,5000,10),(5000,10,9)):
        p=bounded_scale(width,height,glyph)
        assert p['strategy']=='tiles'
        assert p['network_height']<=1800
        assert p['tile_width']*p['network_height']/p['tile_height']<=2401
        xs=tile_starts(width,p['tile_width'],p['overlap_x']);ys=tile_starts(height,p['tile_height'],p['overlap_y'])
        assert xs[0]==ys[0]==0 and xs[-1]+p['tile_width']==width and ys[-1]+p['tile_height']==height
        assert all(b<=a+p['tile_width'] for a,b in zip(xs,xs[1:]))
        assert all(b<=a+p['tile_height'] for a,b in zip(ys,ys[1:]))


def test_small_canvas_keeps_the_same_independent_ink_scale_without_tiling():
    assert bounded_scale(2896,247,31)==dict(strategy='full',network_height=159)
