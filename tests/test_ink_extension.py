import unittest

import cv2
import numpy as np

from bbvlm.refine import extend_words_to_foreground, select_edge_punctuation_extensions


class InkExtensionTest(unittest.TestCase):
    def setUp(self):
        self.gray = np.full((40, 100), 255, np.uint8)
        self.polygon = [[0, 0], [100, 0], [100, 40], [0, 40]]
        self.line_box = [0, 0, 100, 40]

    def test_adds_nearby_terminal_ink_without_shrinking(self):
        cv2.rectangle(self.gray, (10, 12), (24, 27), 0, -1)
        cv2.rectangle(self.gray, (27, 18), (32, 21), 0, -1)
        native = [[10, 12, 25, 28]]
        result, audit = extend_words_to_foreground(
            self.gray, native, self.polygon, self.line_box,
            max_gap_height_ratio=.25)
        self.assertEqual(result, [[10.0, 12.0, 33.0, 28.0]])
        self.assertTrue(audit[0]['changed'])
        self.assertLessEqual(result[0][0], native[0][0])
        self.assertGreaterEqual(result[0][2], native[0][2])

    def test_distant_noise_is_not_absorbed(self):
        cv2.rectangle(self.gray, (10, 12), (24, 27), 0, -1)
        cv2.rectangle(self.gray, (70, 18), (75, 21), 0, -1)
        native = [[10, 12, 25, 28]]
        result, _ = extend_words_to_foreground(
            self.gray, native, self.polygon, self.line_box,
            max_gap_height_ratio=.25)
        self.assertEqual(result, [[10.0, 12.0, 25.0, 28.0]])

    def test_interword_cell_prevents_cross_assignment(self):
        cv2.rectangle(self.gray, (10, 12), (24, 27), 0, -1)
        cv2.rectangle(self.gray, (38, 12), (52, 27), 0, -1)
        # Ink at x=35 belongs to the second cell (boundary x=31.5), but is
        # deliberately too far to expand the second word at this threshold.
        cv2.rectangle(self.gray, (34, 18), (36, 21), 0, -1)
        native = [[10, 12, 25, 28], [38, 12, 53, 28]]
        result, _ = extend_words_to_foreground(
            self.gray, native, self.polygon, self.line_box,
            max_gap_height_ratio=.02)
        self.assertEqual(result, [[10.0, 12.0, 25.0, 28.0],
                                  [38.0, 12.0, 53.0, 28.0]])

    def test_rejects_non_physical_order(self):
        with self.assertRaises(ValueError):
            extend_words_to_foreground(
                self.gray, [[20, 10, 30, 20], [5, 10, 15, 20]],
                self.polygon, self.line_box)

    def test_external_mode_ignores_component_centered_inside_native_box(self):
        # Its right edge extends beyond the native interval, but the component
        # centroid is inside.  External-only mode avoids systematic reboxing.
        cv2.rectangle(self.gray, (20, 12), (30, 27), 0, -1)
        native = [[10, 10, 26, 30]]
        result, _ = extend_words_to_foreground(
            self.gray, native, self.polygon, self.line_box,
            external_centroids_only=True)
        self.assertEqual(result, [[10.0, 10.0, 26.0, 30.0]])

    def test_only_edge_punctuation_routes_extension(self):
        native = [[0, 0, 10, 10], [20, 0, 30, 10], [40, 0, 50, 10]]
        candidate = [[0, 0, 12, 10], [20, 0, 32, 10], [40, 0, 52, 10]]
        result, decisions = select_edge_punctuation_extensions(
            ['word', 'end.', 'A—B'], native, candidate)
        self.assertEqual(result, [[0.0, 0.0, 10.0, 10.0],
                                  [20.0, 0.0, 32.0, 10.0],
                                  [40.0, 0.0, 50.0, 10.0]])
        self.assertEqual([d['selected'] for d in decisions], [False, True, False])


if __name__ == '__main__':
    unittest.main()
