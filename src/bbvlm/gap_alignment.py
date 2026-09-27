"""Experimental recognition-free word localization with an explicit reject path.

Input is image + line polygon + token sequence, never a word-box reference.
Whitespace projections are old, not a novel segmentation algorithm. The purpose
of this ablation is to quantify when CTC can actually be skipped. A proposal is
not verified text/geometry; even a large gap margin can be confidently wrong.
"""
import numpy as np
from .refine import prepare_line_foreground


def locate_words_without_recognizer(gray, polygon, line_box, tokens, *,
                                   min_gap_height_ratio=.10, gap_separation_ratio=1.5):
    if not tokens or any(not isinstance(t, str) or not t or any(c.isspace() for c in t)
                         for t in tokens):
        raise ValueError('nonempty whitespace-free tokens required')
    if min_gap_height_ratio < 0 or gap_separation_ratio <= 1:
        raise ValueError('invalid gap parameters')
    fg, ox, oy = prepare_line_foreground(gray, polygon, line_box)
    occupied = np.flatnonzero((fg > 0).any(axis=0))
    result = {'method': 'projection_gap_no_recognizer_a19', 'status': 'abstain',
              'boxes': [], 'tokens': list(tokens), 'certified': False,
              'recognizer_forwards': 0}
    if not len(occupied):
        return dict(result, reason='no_foreground')
    gaps = [(int(a+1), int(b), int(b-a-1)) for a, b in zip(occupied, occupied[1:]) if b > a+1]
    ranked = sorted(gaps, key=lambda g: (-g[2], g[0]))
    count = len(tokens)-1
    if len(gaps) < count:
        return dict(result, reason='fewer_visible_gaps_than_token_boundaries')
    if count:
        selected = ranked[:count]
        weakest = selected[-1][2]
        rejected_max = ranked[count][2] if count < len(ranked) else 0
        result.update(min_selected_gap=weakest, max_unselected_gap=rejected_max,
                      separation_ratio=weakest/max(1, rejected_max))
        if weakest < min_gap_height_ratio*fg.shape[0]:
            return dict(result, reason='word_gap_too_small')
        if rejected_max and weakest < gap_separation_ratio*rejected_max:
            return dict(result, reason='ambiguous_gap_partition')
        boundaries = sorted((a+b)//2 for a, b, _ in selected)
    else:
        boundaries = []
    cuts = [int(occupied[0])] + boundaries + [int(occupied[-1])+1]
    boxes = []
    for left, right in zip(cuts, cuts[1:]):
        yy, xx = np.nonzero(fg[:, left:right])
        if not len(xx):
            return dict(result, reason='empty_token_interval')
        boxes.append([int(ox+left+xx.min()), int(oy+yy.min()),
                      int(ox+left+xx.max()+1), int(oy+yy.max()+1)])
    return dict(result, status='proposal_requires_review', reason='separated_gaps', boxes=boxes)
