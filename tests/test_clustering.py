import numpy as np

from feedback_app.clustering import (
    b_cubed_metrics,
    cluster_purity,
    pairwise_metrics,
    select_threshold,
    threshold_clusters,
)


def test_threshold_clustering_and_metrics() -> None:
    vectors = np.array([[1, 0], [0.99, 0.01], [0, 1], [0.01, 0.99]], dtype=float)
    labels = threshold_clusters(vectors, 0.9)
    gold = ["A", "A", "B", "B"]
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]
    assert pairwise_metrics(gold, labels)["f1"] == 1
    assert b_cubed_metrics(gold, labels)["f1"] == 1
    assert cluster_purity(gold, labels) == 1


def test_threshold_selection_honors_precision_floor() -> None:
    vectors = np.array([[1, 0], [0.98, 0.02], [0.7, 0.7]], dtype=float)
    result = select_threshold(vectors, ["A", "A", "B"], thresholds=[0.7, 0.9])
    assert result.threshold == 0.9

