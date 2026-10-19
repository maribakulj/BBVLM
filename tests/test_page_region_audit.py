from page_region_audit import coverage,union_area


def test_overlapping_detail_views_cover_source_without_overview():
    region=dict(image='/tmp/whole.png',bbox=[100,200,200,500],views=[
        dict(path='/tmp/a.png',source_bbox=[100,200,200,370]),
        dict(path='/tmp/b.png',source_bbox=[100,350,200,500])])
    meta={'native_history_provenance':{'input_views':{'observed_paths':['/tmp/a.png','/tmp/b.png']}}}
    result=coverage(region,meta)
    assert result['fraction']==1 and result['observed_pixels']==30000
    meta['native_history_provenance']['input_views']['observed_paths'].pop()
    assert coverage(region,meta)['fraction']==170/300


def test_union_never_double_counts_overlap():
    assert union_area([[0,0,20,20],[10,10,30,30]])==700
