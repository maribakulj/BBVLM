from scripts.evaluate_finlam_page_a48 import article_pairs, precedence, prf, title_cut_groups


def test_title_cut_keeps_consecutive_title_run_together():
    classes = [7, 6, 6, 8, 7, 6, 7]
    groups = title_cut_groups(list(range(len(classes))), classes)
    assert [groups[i] for i in range(len(classes))] == [0, 1, 1, 1, 1, 2, 2]


def test_article_pair_metric_penalizes_split_and_merge():
    reference = article_pairs({0: "a", 1: "a", 2: "b", 3: "b"})
    split = article_pairs({0: 0, 1: 1, 2: 2, 3: 2})
    merge = article_pairs({0: 0, 1: 0, 2: 0, 3: 0})
    assert prf(reference, split)["recall"] == 0.5
    assert prf(reference, merge)["precision"] == 1 / 3


def test_precedence_has_explicit_pair_and_edge_denominators():
    score = precedence([0, 1, 2], [1, 0, 2])
    assert score["pairwise_denominator"] == 3
    assert score["pairwise_correct"] == 2
    assert score["reference_adjacent_denominator"] == 2
    assert score["reference_adjacent_correct"] == 1
