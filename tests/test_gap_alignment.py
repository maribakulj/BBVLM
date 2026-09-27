import unittest
import numpy as np
from bbvlm.gap_alignment import locate_words_without_recognizer


class GapAlignmentTests(unittest.TestCase):
    def test_clear_gaps_preserve_ink(self):
        gray = np.full((20, 70), 255, np.uint8)
        gray[4:16, 3:16] = 0
        gray[2:17, 40:60] = 0
        p = locate_words_without_recognizer(gray, [[0,0],[69,0],[69,19],[0,19]], [0,0,70,20], ['abc','def'])
        self.assertEqual(p['boxes'], [[3,4,16,16],[40,2,60,17]])
        self.assertFalse(p['certified'])
        self.assertEqual(p['recognizer_forwards'], 0)

    def test_equal_gaps_abstain(self):
        gray = np.full((20, 70), 255, np.uint8)
        for x in (3, 23, 43):
            gray[4:16, x:x+10] = 0
        p = locate_words_without_recognizer(gray, [[0,0],[69,0],[69,19],[0,19]], [0,0,70,20], ['abc','def'])
        self.assertEqual(p['status'], 'abstain')
        self.assertEqual(p['boxes'], [])

    def test_blank_and_invalid_tokens(self):
        gray = np.full((20,70),255,np.uint8)
        poly = [[0,0],[69,0],[69,19],[0,19]]
        self.assertEqual(locate_words_without_recognizer(gray,poly,[0,0,70,20],['a'])['reason'], 'no_foreground')
        with self.assertRaises(ValueError):
            locate_words_without_recognizer(gray,poly,[0,0,70,20],['a b'])
