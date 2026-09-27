import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as S
import unittest
from lxml import etree as E
from PIL import Image
from bbvlm import document as D
from bbvlm.formats import (import_xml, export_alto, export_mets, validate_xml,
                           audit_mets_package, ALTO, METS, MODS, PREMIS)
from bbvlm.metrics import text_scores, word_scores, spacer
from bbvlm.production import produce, segmentation_graph
from bbvlm.vlm import prepare_batch
from bbvlm.binding import bind_olr_page, bind_semantic_page, bind_role_filter_page, bind_faceted_page, bind_coarse_faceted_page
from bbvlm.semantic import group_header_units, refine_stream_roles_by_height, refine_stream_roles_by_typography
from bbvlm.order import infer_column_major_order
from bbvlm.__main__ import export_package
import alto

ROOT = Path(__file__).resolve().parents[1]


def sample():
    d = D.new_document('sample')
    d['nodes'] = [
        dict(id='P1',kind='page',parent=None,page='P1',bbox=[0,0,100,100],status='automatic',image='page.png'),
        dict(id='R1',kind='region',parent='P1',page='P1',bbox=[1,1,90,90],status='automatic'),
        dict(id='L1',kind='line',parent='R1',page='P1',bbox=[1,1,90,20],status='automatic',text='hello',baseline=[[1,15],[90,15]]),
        dict(id='W1',kind='word',parent='L1',page='P1',bbox=[1,1,30,20],status='automatic',text='hello')]
    return d


def response(text='hello'):
    return dict(requested_line_ids=['L1'],lines=[dict(id='L1',text=text,uncertain=False)])


class GraphTests(unittest.TestCase):
    def test_column_order_is_geometry_only_and_deterministic(self):
        regions=[{'id':'R3','bbox':[60,50,95,80]},
                 {'id':'R1','bbox':[5,10,40,30]},
                 {'id':'R2','bbox':[5,40,40,70]},
                 {'id':'M','bbox':[5,0,95,8]}]
        result=infer_column_major_order(regions,[0,0,100,100],gap_ratio=.2,
                                        top_exclusion_ratio=.09,max_anchor_width_ratio=.5)
        self.assertEqual([x for x in result['ordered_region_ids'] if x!='M'],['R1','R2','R3'])
        self.assertEqual(len(result['reading_order']),len(regions)-1)
        self.assertEqual(set(result['column_by_region']),{'R1','R2','R3','M'})
        with self.assertRaisesRegex(ValueError,'unique'):
            infer_column_major_order(regions+[regions[0]],[0,0,100,100])

    def test_narrow_bridge_does_not_merge_distinct_columns(self):
        regions=[{'id':'L','bbox':[5,10,25,90]}, {'id':'M','bbox':[40,10,60,90]},
                 {'id':'bridge','bbox':[60,40,61,60]}, {'id':'R','bbox':[75,5,95,90]}]
        merged=infer_column_major_order(regions,[0,0,100,100],gap_ratio=.25,
                                        top_exclusion_ratio=0,max_anchor_width_ratio=.5)
        split=infer_column_major_order(regions,[0,0,100,100],gap_ratio=.25,
                                       top_exclusion_ratio=0,max_anchor_width_ratio=.5,
                                       min_anchor_width_ratio=.1)
        self.assertEqual(len(merged['column_anchors_x']),2)
        self.assertEqual(len(split['column_anchors_x']),3)

    def test_visual_token_binding_is_strict_and_hides_stable_ids(self):
        binding={'Q7':'R_long_internal_1','M2':'R_long_internal_2'}
        response={'page':'P','ordered_tokens':['M2','Q7'],
                  'groups':[{'id':'G1','tokens':['Q7','M2']}],
                  'roles':{'Q7':'TEXT','M2':'HEADER'},'uncertain_tokens':['Q7']}
        self.assertNotIn('R_long_internal',json.dumps(response))
        bound=bind_olr_page(response,binding)
        self.assertEqual(bound['ordered_region_ids'],['R_long_internal_2','R_long_internal_1'])
        bad=copy.deepcopy(response);bad['ordered_tokens']=['M2','M2']
        with self.assertRaisesRegex(ValueError,'exactly once'):bind_olr_page(bad,binding)
        bad=copy.deepcopy(response);bad['roles']['Q7']='ARTICLE'
        with self.assertRaisesRegex(ValueError,'controlled'):bind_olr_page(bad,binding)
        bad=copy.deepcopy(response);bad['groups'][0]['id']=''
        with self.assertRaisesRegex(ValueError,'group IDs'):bind_olr_page(bad,binding)

    def test_semantic_binding_omits_order_and_validates_eligibility(self):
        binding={'Q7':'R_long_internal_1','M2':'R_long_internal_2'}
        response={'page':'P','eligible_tokens':['M2'],
                  'groups':[{'id':'G1','tokens':['Q7','M2'],'kind':'ARTICLE'}],
                  'roles':{'Q7':'MASTHEAD','M2':'TEXT'},'uncertain_tokens':['Q7']}
        bound=bind_semantic_page(response,binding)
        self.assertEqual(bound['eligible_region_ids'],['R_long_internal_2'])
        self.assertNotIn('ordered_region_ids',bound)
        bad=copy.deepcopy(response);bad['eligible_tokens']=['M2','M2']
        with self.assertRaisesRegex(ValueError,'unique subset'):bind_semantic_page(bad,binding)
        bad=copy.deepcopy(response);bad['groups'][0]['kind']='STORY'
        with self.assertRaisesRegex(ValueError,'controlled'):bind_semantic_page(bad,binding)

    def test_minimal_role_filter_binding_and_header_units(self):
        binding={'Q7':'M','M2':'H1','B4':'H2','X9':'T','Z3':'H3','C8':'T2'}
        response={'page':'P','eligible_tokens':['M2','B4','X9','Z3','C8'],
                  'roles':{'Q7':'MASTHEAD','M2':'HEADER','B4':'HEADER','X9':'TEXT','Z3':'HEADER','C8':'TEXT'},
                  'uncertain_tokens':[]}
        bound=bind_role_filter_page(response,binding)
        regions=[{'id':'M','bbox':[0,0,100,5]}, {'id':'H1','bbox':[0,10,30,20]},
                 {'id':'H2','bbox':[0,18,30,25]}, {'id':'T','bbox':[0,26,30,50]},
                 {'id':'H3','bbox':[0,60,30,70]}, {'id':'T2','bbox':[0,71,30,90]}]
        result=group_header_units(regions,[0,0,100,100],bound['roles'],bound['eligible_region_ids'],
                                  gap_ratio=.2,top_exclusion_ratio=0,max_anchor_width_ratio=.5)
        self.assertEqual([g['region_ids'] for g in result['groups']],[['M'],['H1','H2','T'],['H3','T2']])
        bad=copy.deepcopy(response);bad['eligible_tokens']=['M2','M2']
        with self.assertRaisesRegex(ValueError,'unique subset'):bind_role_filter_page(bad,binding)

    def test_header_units_partition_masthead_even_if_filter_is_wrong(self):
        regions=[{'id':'M','bbox':[0,0,100,8]}, {'id':'H','bbox':[0,15,45,25]},
                 {'id':'T','bbox':[0,28,45,60]}]
        roles={'M':'MASTHEAD','H':'HEADER','T':'TEXT'}
        result=group_header_units(regions,[0,0,100,100],roles,['M','H','T'],
                                  gap_ratio=.14,top_exclusion_ratio=.055,
                                  max_anchor_width_ratio=.55)
        self.assertEqual([g['region_ids'] for g in result['groups']],[['M'],['H','T']])

    def test_faceted_binding_keeps_editorial_genre_out_of_physical_role(self):
        binding={'Q7':'H','M2':'T'}
        response={'page':'P','physical_roles':{'Q7':'HEADER','M2':'TEXT'},
                  'editorial_genres':{'Q7':'ADVERT','M2':'ADVERT'},
                  'uncertain_physical_tokens':[],'uncertain_genre_tokens':['M2']}
        bound=bind_faceted_page(response,binding)
        self.assertEqual(bound['physical_roles'],{'H':'HEADER','T':'TEXT'})
        self.assertEqual(bound['editorial_genres'],{'H':'ADVERT','T':'ADVERT'})
        self.assertEqual(bound['uncertain_genre_region_ids'],['T'])
        self.assertNotIn('eligible_region_ids',bound)
        bad=copy.deepcopy(response);bad['physical_roles']['Q7']='ADVERT'
        with self.assertRaisesRegex(ValueError,'physical_roles'):bind_faceted_page(bad,binding)

    def test_coarse_faceted_binding_and_frozen_height_refinement(self):
        binding={'Q7':'H','M2':'T','X9':'M'}
        response={'page':'P','coarse_roles':{'Q7':'STREAM','M2':'STREAM','X9':'MASTHEAD'},
                  'editorial_genres':{'Q7':'ADVERT','M2':'ADVERT','X9':'MASTHEAD'},
                  'uncertain_coarse_tokens':[],'uncertain_genre_tokens':['M2']}
        bound=bind_coarse_faceted_page(response,binding)
        regions=[{'id':'H','bbox':[0,10,40,12]}, {'id':'T','bbox':[0,20,40,45]},
                 {'id':'M','bbox':[0,0,100,8]}]
        roles=refine_stream_roles_by_height(regions,[0,0,100,100],bound['coarse_roles'],
                                            max_header_height_page_ratio=.02)
        self.assertEqual(roles,{'H':'HEADER','T':'TEXT','M':'MASTHEAD'})
        self.assertEqual(bound['editorial_genres']['H'],'ADVERT')
        bad=copy.deepcopy(response);bad['coarse_roles']['Q7']='HEADER'
        with self.assertRaisesRegex(ValueError,'coarse_roles'):bind_coarse_faceted_page(bad,binding)
        with self.assertRaisesRegex(ValueError,'positive'):
            refine_stream_roles_by_height(regions,[0,0,100,100],bound['coarse_roles'],
                                          max_header_height_page_ratio=0)

    def test_typography_refinement_keeps_multiline_title(self):
        regions=[{'id':'H','bbox':[0,0,40,30]},{'id':'T','bbox':[0,30,40,90]},
                 {'id':'O','bbox':[40,0,80,20]}]
        coarse={'H':'STREAM','T':'STREAM','O':'OTHER'}
        features={
            'H':{'line_count':2,'median_line_height_page_ratio':.011,'uppercase_ratio':1.0},
            'T':{'line_count':5,'median_line_height_page_ratio':.012,'uppercase_ratio':.1},
            'O':{'line_count':1,'median_line_height_page_ratio':.020,'uppercase_ratio':1.0}}
        roles=refine_stream_roles_by_typography(
            regions,coarse,features,max_header_line_count=2,
            min_median_line_height_page_ratio=.014,min_uppercase_ratio=.8)
        self.assertEqual(roles,{'H':'HEADER','T':'TEXT','O':'OTHER'})
        with self.assertRaisesRegex(ValueError,'cover every region'):
            refine_stream_roles_by_typography(
                regions,coarse,{'H':features['H']},max_header_line_count=2,
                min_median_line_height_page_ratio=.014,min_uppercase_ratio=.8)

    def test_spacer_character_count_formula(self):
        self.assertEqual(spacer("abc", "abc"), 0)
        self.assertAlmostEqual(spacer("abc", "ab"), 1/3)
        self.assertAlmostEqual(spacer("abc", "abd"), 1/3)
        self.assertIsNone(spacer("", "abc"))

    def test_text_change_invalidates_geometry_and_records_previous(self):
        d=sample();out=D.apply_proposal(d,response('world'),'test')
        self.assertEqual(len(D.children(out,'L1','word')),0)
        self.assertTrue(D.index(out)['L1']['needs_alignment'])
        self.assertEqual(out['events'][0]['previous_words'][0]['text'],'hello')
        self.assertEqual(D.index(d)['L1']['text'],'hello')

    def test_same_text_preserves_alignment_without_verification(self):
        out=D.apply_proposal(sample(),response(),'test')
        self.assertEqual(len(D.children(out,'L1','word')),1)
        self.assertEqual(D.index(out)['L1']['status'],'automatic')

    def test_cannot_overwrite_human_text(self):
        d=sample();D.index(d)['L1']['status']='human_verified'
        with self.assertRaises(ValueError):D.apply_proposal(d,response('changed'),'test')

    def test_missing_line_cannot_be_hidden_by_changing_echoed_request(self):
        with self.assertRaises(ValueError):D.apply_proposal(sample(),dict(requested_line_ids=[],lines=[]),'test')

    def test_duplicate_and_unknown_response_ids(self):
        r=response();r['lines']*=2
        with self.assertRaises(ValueError):D.apply_proposal(sample(),r,'test')
        r=response();r['lines'][0]['id']='unknown'
        with self.assertRaises(ValueError):D.apply_proposal(sample(),r,'test')

    def test_cycle_rejected_atomically(self):
        d=sample();d['nodes'].append(dict(id='R2',kind='region',parent='P1',page='P1',bbox=[2,30,90,60],status='automatic'))
        r=response();r['reading_order']=[dict(before='R1',after='R2'),dict(before='R2',after='R1')]
        with self.assertRaisesRegex(ValueError,'cycle'):D.apply_proposal(d,r,'test')
        self.assertEqual(d['reading_order'],[])

    def test_observed_metadata_requires_known_evidence(self):
        for refs in [[],['invented']]:
            d=sample();d['metadata']=[dict(field='date',value='1900',category='observed',evidence=refs)]
            with self.assertRaises(ValueError):D.validate(d)

    def test_out_of_bounds_geometry_rejected(self):
        d=sample();D.index(d)['W1']['bbox'][2]=101
        with self.assertRaises(ValueError):D.validate(d)

    def test_missing_word_alignment_stays_in_review(self):
        d=sample();d['nodes']=d['nodes'][:-1];D.index(d)['L1']['status']='rejected'
        self.assertIn('missing_word_alignment',D.review_queue(d)[0]['reasons'])


class ExportTests(unittest.TestCase):
    def validate_alto(self,b):validate_xml(b,ROOT/'schemas/alto-4-4.xsd')

    def test_aligned_output_schema_and_half_open_width(self):
        b=export_alto(sample(),'P1');self.validate_alto(b)
        r=E.fromstring(b);w=r.find('.//{%s}String'%ALTO)
        self.assertEqual(w.get('WIDTH'),'29')

    def test_unaligned_and_rejected_lines_remain_in_xml(self):
        d=sample();d['nodes']=d['nodes'][:-1];D.index(d)['L1']['text']='';D.index(d)['L1']['status']='rejected'
        b=export_alto(d,'P1');self.validate_alto(b)
        r=E.fromstring(b);self.assertEqual(len(r.findall('.//{%s}TextLine'%ALTO)),1)
        self.assertEqual(r.find('.//{%s}String'%ALTO).get('TAGREFS'),'UNALIGNED')
        self.assertIsNone(r.find('.//{%s}String'%ALTO).get('HPOS'))

    def test_empty_page_schema_valid(self):
        d=sample();d['nodes']=d['nodes'][:1];self.validate_alto(export_alto(d,'P1'))
        self.validate_alto(alto.build(100,100,'page.png',[],'test','no accepted lines'))

    def test_mets_area_resolves_to_alto_region(self):
        d=sample();d['articles']=[dict(id='A1',title='title',regions=['R1'])]
        d['metadata']=[dict(field='title',value='hello',category='observed',evidence=['L1'])]
        b=export_mets(d,{'P1':'P1.alto.xml'});validate_xml(b,ROOT/'schemas/mets.xsd')
        area=E.fromstring(b).find('.//{%s}area'%METS)
        self.assertEqual(area.get('FILEID'),'FILE_P1')
        self.assertIn(area.get('BEGIN'),E.fromstring(export_alto(d,'P1')).xpath('//@ID'))

    def test_mets_mods_premis_image_and_fixity_profile(self):
        d=sample();d['metadata']=[dict(field='title',value='Evidence title',
            category='observed',evidence=['L1'],source='test fixture')]
        with tempfile.TemporaryDirectory() as td:
            out=Path(td); summary=export_package(d,out,ROOT/'schemas')
            root=E.parse(str(out/'mets.xml'))
            self.assertEqual(root.findtext('.//{%s}title'%MODS),'Evidence title')
            self.assertEqual(root.find('.//{%s}premis'%PREMIS).get('version'),'3.0')
            uses={g.get('USE') for g in root.findall('.//{%s}fileGrp'%METS)}
            self.assertTrue({'OCR','MASTER_IMAGE','DOCUMENT_GRAPH','RETRIEVAL_INDEX'}<=uses)
            page=root.find(".//{%s}structMap[@TYPE='PHYSICAL']//{%s}div[@TYPE='page']"%(METS,METS))
            self.assertEqual(len(page.findall('{%s}fptr'%METS)),2)
            self.assertEqual(summary['mets_package_integrity']['checksums_verified'],3)
            self.assertEqual(summary['mets_package_integrity']['unresolved_unchecksummed_local_uris'],1)
            self.assertTrue(summary['embedded_profile_validation']['premis_3_xsd_valid'])
            self.assertFalse(summary['embedded_profile_validation']['mods_3_8_xsd_valid'])

    def test_mets_fixity_audit_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);export_package(sample(),out,ROOT/'schemas')
            (out/'document.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'fixity mismatch'):
                audit_mets_package((out/'mets.xml').read_bytes(),out)

    def test_only_unambiguous_total_reading_order_is_exported(self):
        d=sample()
        d['nodes'].append(dict(id='R2',kind='region',parent='P1',page='P1',bbox=[5,40,90,80],status='automatic'))
        b=export_alto(d,'P1');self.assertIsNone(E.fromstring(b).find('{%s}ReadingOrder'%ALTO))
        d['reading_order']=[dict(before='R2',after='R1')]
        b=export_alto(d,'P1');self.validate_alto(b)
        self.assertEqual([r.get('REF') for r in E.fromstring(b).findall('.//{%s}ElementRef'%ALTO)],['R2','R1'])

    def test_pero_legacy_scalar_baseline_is_importable(self):
        raw=b'''<alto xmlns="http://www.loc.gov/standards/alto/ns-v2#"><Description><MeasurementUnit>pixel</MeasurementUnit></Description><Layout><Page WIDTH="100" HEIGHT="100"><PrintSpace><TextBlock HPOS="1" VPOS="1" WIDTH="80" HEIGHT="30"><TextLine HPOS="1" VPOS="1" WIDTH="80" HEIGHT="20" BASELINE="15"><String CONTENT="word" HPOS="1" VPOS="1" WIDTH="30" HEIGHT="20"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'''
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'native.xml';p.write_bytes(raw);d=import_xml(p)
            ln=next(n for n in d['nodes'] if n['kind']=='line')
            self.assertEqual(ln['baseline'],[[1.,15.],[81.,15.]])
            self.validate_alto(export_alto(d,'P0001'))

    def test_custom_ssu_and_order_import_as_evidence_not_articles(self):
        raw=b'''<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Description><MeasurementUnit>pixel</MeasurementUnit></Description><Layout><Page WIDTH="100" HEIGHT="100"><PrintSpace><TextBlock ID="b0" HPOS="1" VPOS="1" WIDTH="80" HEIGHT="20" BLOCK_TYPE="HEADER" SSU_ID="story_1" READING_ORDER="0"><TextLine ID="l0" HPOS="1" VPOS="1" WIDTH="80" HEIGHT="10"><String CONTENT="head" HPOS="1" VPOS="1" WIDTH="20" HEIGHT="10"/></TextLine></TextBlock><TextBlock ID="b1" HPOS="1" VPOS="30" WIDTH="80" HEIGHT="20" BLOCK_TYPE="TEXT" SSU_ID="story_1" READING_ORDER="1"><TextLine ID="l1" HPOS="1" VPOS="30" WIDTH="80" HEIGHT="10"><String CONTENT="body" HPOS="1" VPOS="30" WIDTH="20" HEIGHT="10"/></TextLine></TextBlock><TextBlock ID="mast" HPOS="1" VPOS="60" WIDTH="80" HEIGHT="20" BLOCK_TYPE="MASTHEAD" SSU_ID="masthead" READING_ORDER="-1"><TextLine ID="lm" HPOS="1" VPOS="60" WIDTH="80" HEIGHT="10"><String CONTENT="mast" HPOS="1" VPOS="60" WIDTH="20" HEIGHT="10"/></TextLine></TextBlock></PrintSpace></Page></Layout></alto>'''
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'custom.xml';p.write_bytes(raw);d=import_xml(p)
            self.assertEqual(len(d['semantic_units']),2)
            story=next(x for x in d['semantic_units'] if x['label']=='story_1')
            self.assertEqual(len(story['regions']),2)
            self.assertEqual(d['articles'],[])
            self.assertEqual(len(d['reading_order']),1)
            self.assertEqual([n['role'] for n in d['nodes'] if n['kind']=='region'],['header','text','masthead'])
            self.validate_alto(export_alto(d,'P0001'))
            mets=export_mets(d,{'P0001':'P0001.xml'});validate_xml(mets,ROOT/'schemas/mets.xsd')
            types=E.fromstring(mets).xpath('//@TYPE')
            self.assertIn('semantic-unit',types);self.assertNotIn('article',types)

    def test_legacy_synthetic_is_not_fake_probability_and_no_implicit_hyphen(self):
        lines=[dict(id='L1',bbox=[1,1,20,9],words=[dict(text='pre-',x0=1,y0=1,x1=20,y1=9,synthetic=True)]),
               dict(id='L2',bbox=[1,11,20,19],words=[dict(text='fix',x0=1,y0=11,x1=20,y1=19)])]
        blocks=[dict(id='B1',x0=1,y0=1,x1=20,y1=19,lines=lines)]
        b=alto.build(100,100,'x.png',blocks,'test','test');self.validate_alto(b)
        root=E.fromstring(b);w=root.find('.//{%s}String'%ALTO)
        self.assertIsNone(w.get('WC'));self.assertIsNone(w.get('SUBS_TYPE'))
        self.assertEqual(w.get('TAGREFS'),'SYNTHETIC_WORD')

    def test_real_repository_outputs_import_and_validate(self):
        names=['out-pp','out-vt','out-fraktur','out-finale']
        if any(not (ROOT/name/'page.alto.xml').exists() for name in names):
            self.skipTest('large original repository outputs are omitted from portable checkpoint')
        for name in names:
            d=import_xml(ROOT/name/'page.alto.xml');self.validate_alto(export_alto(d,'P0001'))
            self.assertEqual(len(D.review_queue(d)),sum(n['kind']=='line' for n in d['nodes']))

    def test_onb_preserves_all_baselines_and_single_word_headers(self):
        d=import_xml(ROOT/'experiments/terra_luna/reference/page.xml')
        lines=[n for n in d['nodes'] if n['kind']=='line']
        self.assertEqual(len(lines),354)
        self.assertTrue(any(len(n['text'].split())==1 for n in lines))
        self.assertTrue(any(n['baseline'] for n in lines))
        self.validate_alto(export_alto(d,'P0001'))


class MetricsTests(unittest.TestCase):
    def test_missing_lines_are_errors_not_dropped(self):
        s=text_scores([dict(id='L1',text='abc'),dict(id='L2',text='de')],[dict(id='L1',text='abc')])
        self.assertEqual(s['cer'],2/5);self.assertEqual(s['missing_lines'],1)

    def test_normalisation_is_reported_separately(self):
        s=text_scores([dict(id='L',text='ſ⸗')],[dict(id='L',text='s-')])
        self.assertEqual(s['cer'],1);self.assertEqual(s['cer_nfc_long_s'],.5)

    def test_joint_text_geometry_counts_missing_and_duplicate_predictions(self):
        r=sample();h=sample();h['nodes']+= [dict(h['nodes'][-1],id='W2')]
        s=word_scores(r,h);self.assertEqual(s['recall'],1);self.assertEqual(s['precision'],.5)
        h['nodes']=h['nodes'][:-2];self.assertEqual(word_scores(r,h)['recall'],0)

    def test_line_only_reference_refuses_word_score(self):
        r=sample();r['nodes']=r['nodes'][:-1]
        with self.assertRaises(ValueError):word_scores(r,sample())


class ProductionTests(unittest.TestCase):
    def segmentation(self):
        return S(regions={'body':[S(id='r',boundary=[(1,1),(95,1),(95,95),(1,95)])]},lines=[
            S(id='source1',regions=['r'],boundary=[(1,1),(90,1),(90,20),(1,20)],baseline=[(1,15),(90,15)]),
            S(id='source2',regions=['r'],boundary=[(1,30),(90,30),(90,49),(1,49)],baseline=[(1,45),(90,45)])])

    def test_preserves_geometry_and_no_global_y_sort(self):
        seg=self.segmentation();seg.lines.reverse()
        d=segmentation_graph(seg,100,100,'x.png')
        self.assertEqual(D.index(d)['L0001']['source_id'],'source2')
        self.assertEqual(D.index(d)['L0001']['baseline'],[[1,45],[90,45]])

    def test_id_batch_rejects_count_preserving_wrong_ids(self):
        def reader(crop,ids):return {'wrong1':'abc','wrong2':'def'},1.
        reader.returns_ids=True
        boxer=S(name='never-called',boxes=lambda *args:self.fail('must not align wrong line IDs'))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);Image.new('RGB',(100,100),'white').save(p/'x.png')
            s=produce(str(p/'x.png'),p/'out',reader,boxer,segmentation=self.segmentation(),verbose=False)
            d=D.load(p/'out/document.json')
            self.assertEqual(s['lignes_ecartees'],2);self.assertEqual(len(D.review_queue(d)),2)
            validate_xml((p/'out/page.alto.xml').read_bytes(),ROOT/'schemas/alto-4-4.xsd')

    def test_limit_retains_unprocessed_lines_and_legacy_reader_is_single_line(self):
        calls=[]
        def reader(crop,n):calls.append(n);return ['hello'],1.
        boxer=S(name='fixture',boxes=lambda gray,line:[(2,2,15,10)])
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);Image.new('RGB',(100,100),'white').save(p/'x.png')
            s=produce(str(p/'x.png'),p/'out',reader,boxer,max_lines=1,segmentation=self.segmentation(),verbose=False)
            d=D.load(p/'out/document.json')
            self.assertEqual(calls,[1]);self.assertEqual(s['lignes_detectees'],2)
            self.assertEqual(D.index(d)['L0002']['status'],'pending')

    def test_blind_request_does_not_expose_source_text(self):
        d=sample()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);Image.new('RGB',(100,100),'white').save(p/'x.png')
            request=prepare_batch(d,p/'x.png','P1',['L1'],p/'request')
            self.assertNotIn('hello',json.dumps(request))
            self.assertEqual(request['requested_line_ids'],['L1'])


if __name__ == '__main__':unittest.main()
