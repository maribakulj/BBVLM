import unittest
from bbvlm.columns import propose_column_windows,route_lines_to_columns

CONFIG=dict(gap_ratio=.14,top_exclusion_ratio=.055,max_anchor_width_ratio=.55,
            min_anchor_width_ratio=.02,assign_by_overlap=True)


class ColumnTests(unittest.TestCase):
    def test_route_preserves_crossing_lines_and_abstains(self):
        windows=[dict(id='a',core_bbox=[0,0,50,100],context_bbox=[0,0,52,100]),
                 dict(id='b',core_bbox=[50,0,100,100],context_bbox=[48,0,100,100])]
        lines=[dict(id='s',bbox=[10,10,90,20],polygon=[[10,10],[90,11],[90,20],[10,20]]),
               dict(id='l',bbox=[10,25,53,35])]
        r=route_lines_to_columns(lines,windows,[0,0,100,100])
        self.assertIsNone(r['lines'][0]['column_id'])
        self.assertEqual(r['lines'][0]['crop_bbox'],lines[0]['bbox'])
        self.assertEqual(r['lines'][1]['column_id'],'a')
        self.assertFalse(r['lines'][1]['context_contains_line'])
        self.assertEqual(r['lines'][1]['source_line'],lines[1])
        r['lines'][0]['source_line']['polygon'][0][0]=0
        self.assertEqual(lines[0]['polygon'][0][0],10)

    def test_route_flags_outside_image_instead_of_silent_geometry_repair(self):
        w=[dict(id='a',core_bbox=[0,0,100,100],context_bbox=[0,0,100,100])]
        line=dict(id='x',bbox=[-3,5,30,20])
        r=route_lines_to_columns([line],w,[0,0,100,100])['lines'][0]
        self.assertIn('source_geometry_outside_image',r['review_reasons'])
        self.assertEqual(r['source_line']['bbox'],[-3,5,30,20])
        self.assertEqual(r['crop_bbox'],[0,5,30,20])
        with self.assertRaises(ValueError):route_lines_to_columns([line,line],w,[0,0,100,100])

    def test_spanning_title_preserved_without_merging_columns(self):
        det=[dict(id='l',bbox=[5,20,45,90],class_name='plain text'),
             dict(id='r',bbox=[55,20,95,90],class_name='plain text'),
             dict(id='h',bbox=[5,5,95,15],class_name='title'),
             dict(id='f',bbox=[60,92,80,98],class_name='abandon')]
        result=propose_column_windows(det,[0,0,100,100],order_parameters=CONFIG)
        self.assertEqual(len(result['windows']),2)
        self.assertEqual(result['spanning_region_ids'],['h'])
        self.assertEqual(set(result['retained_detection_ids']),{'l','r','h','f'})
        self.assertEqual(result['windows'][0]['context_bbox'][0],0)
        self.assertEqual(result['windows'][-1]['context_bbox'][2],100)
        self.assertGreater(result['windows'][0]['context_bbox'][2],
                           result['windows'][1]['context_bbox'][0])
        self.assertIsNone(result['word_boxes'])

    def test_empty_or_nonbody_falls_back_without_loss(self):
        for detections in ([],[dict(id='x',bbox=[5,5,20,20],class_name='figure')]):
            result=propose_column_windows(detections,[0,0,100,100],order_parameters=CONFIG)
            self.assertTrue(result['requires_layout_review'])
            self.assertEqual(result['windows'][0]['context_bbox'],[0,0,100,100])

    def test_invalid_and_duplicate_rejected(self):
        d=dict(id='a',bbox=[1,2,10,20],class_name='plain text')
        for rows in ([d,d],[dict(d,bbox=[1,2,float('nan'),20])],
                     [dict(d,bbox=[-1,2,10,20])]):
            with self.assertRaises(ValueError):
                propose_column_windows(rows,[0,0,100,100],order_parameters=CONFIG)

    def test_input_order_does_not_change_windows(self):
        d=[dict(id='l',bbox=[5,20,45,90],class_name='plain text'),
           dict(id='r',bbox=[55,20,95,90],class_name='plain text')]
        a=propose_column_windows(d,[0,0,100,100],order_parameters=CONFIG)
        b=propose_column_windows(d[::-1],[0,0,100,100],order_parameters=CONFIG)
        self.assertEqual(a['windows'],b['windows'])
