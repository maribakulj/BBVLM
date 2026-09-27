import unittest
from bbvlm.ocr_conventions import transform, private_use_inventory


class ConventionTests(unittest.TestCase):
    def test_historical_distinctions_survive(self):
        source = '\ue42c ſ ꝛ u v I J ⸗ \uf1e8 \ue8bf'
        result = transform(source, 'glyph_decomposition_v1')
        self.assertEqual(result, 'a\u0364 ſ ꝛ u v I J ⸗ \uf1e8 \ue8bf')
        self.assertNotEqual(result[0:2], 'ä')
        self.assertEqual(private_use_inventory(result), {'U+E8BF': 1, 'U+F1E8': 1})

    def test_source_examples_and_idempotence(self):
        source = 'Na\uf502 \ueedc \ueba6 e\u0301'
        result = transform(source, 'glyph_decomposition_v1')
        self.assertEqual(result, 'Nach tz ſſ é')
        self.assertEqual(transform(result, 'glyph_decomposition_v1'), result)
        self.assertEqual(transform(source), source)

    def test_unknown_profile_rejected(self):
        with self.assertRaises(ValueError):
            transform('text', 'favorable')
