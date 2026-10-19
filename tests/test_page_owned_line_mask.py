import numpy as np
from page_owned_line_mask import owned_crop


def test_paper_noise_is_removed_without_creating_ink_or_changing_source():
    gray=np.full((60,140),210,np.uint8)
    gray[15:40,15:45]=15;gray[15:40,70:100]=15
    gray[27:29,:]=170
    # Rétablir les glyphes au passage du voile gris.
    gray[15:40,15:45]=15;gray[15:40,70:100]=15
    row=dict(id='a',bbox=[0,0,140,60],baseline=[[0,40],[140,40]])
    before=gray.copy();clean,proof=owned_crop(gray,row,[row])
    assert np.array_equal(gray,before)
    assert np.all(clean>=gray)
    assert np.all(clean[:,50:65]==255)
    assert np.all(clean[15:40,15:45]==15)
    assert not proof['new_dark_pixels']
