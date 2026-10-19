from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from block_ctc import prefix_loglik, solve_gap


class Fake:
    """Probabilités simulées : chaque ligne « imprime » nettement son texte."""
    def __init__(self, truth):
        self.codec = {ch: [i+1] for i, ch in enumerate(sorted(set(''.join(truth.values()))))}
        self.truth = truth

    def encode(self, text):
        text = ' '.join(text.split())
        return [self.codec[c][0] for c in text if c in self.codec], 0

    def logp(self, line_id):
        labels, _ = self.encode(self.truth[line_id])
        C = len(self.codec)+1
        frames = []
        for lab in labels:
            for target in (0, lab, lab, 0):
                row = np.full(C, np.log(.01/(C-1)))
                row[target] = np.log(.99)
                frames.append(row)
        if not frames:  # ligne sans encre
            frames = [np.full(C, np.log(.01/(C-1)))]*8
            for f in frames:
                f[0] = np.log(.99)
        return np.array(frames)


def test_prefix_loglik_peaks_at_true_length():
    fake = Fake({'L': 'abc'})
    scores = prefix_loglik(fake.logp('L'), fake.encode('abcd')[0])
    assert int(np.argmax(scores)) == 3


def test_gap_text_is_cut_where_the_image_says_and_unseen_text_is_skipped():
    truth = {'A': 'Pacific Central', 'B': '113 1/2', 'C': '114 ..', 'N': ''}
    fake = Fake(truth)
    lines = [{'id': k} for k in ('A', 'B', 'N', 'C')]
    text = 'Pacific Central 113 1/2 ligne absente 114 ..'
    result = solve_gap(lines, text, fake)
    pieces = {lines[k]['id']: text[a:b] for k, a, b, _ in result}
    assert pieces == {'A': 'Pacific Central', 'B': '113 1/2', 'C': '114 ..'}


def test_fraction_bar_is_optional_when_the_print_has_a_single_glyph():
    fake = Fake({'L': '12 14'})          # l'image « 12 ¼ » lue sans barre
    fake.codec['/'] = [len(fake.codec)+1]
    labels = [fake.codec[c][0] for c in '12 1'] + [-fake.codec['/'][0]] + [fake.codec['4'][0]]
    logp = fake.logp('L')
    logp = np.concatenate([logp, np.full((logp.shape[0], 1), np.log(1e-4))], axis=1)
    with_optional = prefix_loglik(logp, labels)[-1]
    strict = prefix_loglik(logp, [abs(c) for c in labels])[-1]
    assert with_optional > strict + 3


def test_leader_dots_match_any_printed_count():
    from block_ctc import REPEAT, Posteriors
    # imprimé « a...b » (trois points) ; Gemini écrit huit points
    codec = {'a': [1], '.': [2], 'b': [3]}
    printed = [1, 2, 2, 2, 3]
    C = 4
    frames = []
    for lab in printed:
        for target in (0, lab, 0):
            row = np.full(C, np.log(.01/(C-1)))
            row[target] = np.log(.99)
            frames.append(row)
    logp = np.array(frames)
    p = Posteriors.__new__(Posteriors)
    p.codec, p.keys = codec, sorted(codec, key=len, reverse=True)
    labels, _ = p.encode('a........b')
    assert labels == [1, 2 + REPEAT, 3]
    free = prefix_loglik(logp, labels)[-1]
    counted = prefix_loglik(logp, [1] + [2]*8 + [3])[-1]
    exact = prefix_loglik(logp, printed)[-1]
    assert free > counted + 10
    assert abs(free - exact) < 1.0
