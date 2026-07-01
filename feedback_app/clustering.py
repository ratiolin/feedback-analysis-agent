from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vectors / norms


def threshold_clusters(vectors: np.ndarray, threshold: float) -> list[int]:
    vectors = normalize_vectors(np.asarray(vectors, dtype=float))
    parent = list(range(len(vectors)))

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    similarities = vectors @ vectors.T
    for left in range(len(vectors)):
        for right in range(left + 1, len(vectors)):
            if similarities[left, right] >= threshold:
                union(left, right)
    roots: dict[int, int] = {}
    labels: list[int] = []
    for item in range(len(vectors)):
        root = find(item)
        roots.setdefault(root, len(roots))
        labels.append(roots[root])
    return labels


def pairwise_metrics(gold: list[str], predicted: list[int]) -> dict[str, float]:
    true_positive = false_positive = false_negative = 0
    for left in range(len(gold)):
        for right in range(left + 1, len(gold)):
            same_gold = gold[left] == gold[right]
            same_predicted = predicted[left] == predicted[right]
            if same_gold and same_predicted:
                true_positive += 1
            elif not same_gold and same_predicted:
                false_positive += 1
            elif same_gold and not same_predicted:
                false_negative += 1
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0
    recall = true_positive / recall_denominator if recall_denominator else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"precision": precision, "recall": recall, "f1": f1}


def b_cubed_metrics(gold: list[str], predicted: list[int]) -> dict[str, float]:
    gold_members: dict[str, set[int]] = defaultdict(set)
    predicted_members: dict[int, set[int]] = defaultdict(set)
    for index, (gold_label, predicted_label) in enumerate(zip(gold, predicted, strict=True)):
        gold_members[gold_label].add(index)
        predicted_members[predicted_label].add(index)
    precisions: list[float] = []
    recalls: list[float] = []
    for index, (gold_label, predicted_label) in enumerate(zip(gold, predicted, strict=True)):
        intersection = gold_members[gold_label] & predicted_members[predicted_label]
        precisions.append(len(intersection) / len(predicted_members[predicted_label]))
        recalls.append(len(intersection) / len(gold_members[gold_label]))
    precision = sum(precisions) / len(precisions)
    recall = sum(recalls) / len(recalls)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"precision": precision, "recall": recall, "f1": f1}


def cluster_purity(gold: list[str], predicted: list[int]) -> float:
    clusters: dict[int, list[str]] = defaultdict(list)
    for gold_label, predicted_label in zip(gold, predicted, strict=True):
        clusters[predicted_label].append(gold_label)
    correct = sum(Counter(labels).most_common(1)[0][1] for labels in clusters.values())
    return correct / len(gold) if gold else 0


@dataclass(frozen=True)
class ThresholdResult:
    threshold: float
    labels: list[int]
    pairwise: dict[str, float]
    b_cubed: dict[str, float]
    purity: float


def select_threshold(
    vectors: np.ndarray,
    gold: list[str],
    thresholds: list[float] | None = None,
    minimum_pairwise_precision: float = 0.80,
) -> ThresholdResult:
    thresholds = thresholds or [round(value / 100, 2) for value in range(30, 91, 5)]
    candidates: list[ThresholdResult] = []
    for threshold in thresholds:
        labels = threshold_clusters(vectors, threshold)
        pairwise = pairwise_metrics(gold, labels)
        candidates.append(
            ThresholdResult(
                threshold=threshold,
                labels=labels,
                pairwise=pairwise,
                b_cubed=b_cubed_metrics(gold, labels),
                purity=cluster_purity(gold, labels),
            )
        )
    eligible = [
        item
        for item in candidates
        if item.pairwise["precision"] >= minimum_pairwise_precision
        and item.pairwise["recall"] > 0
    ]
    pool = eligible or candidates
    return max(pool, key=lambda item: (item.b_cubed["f1"], item.pairwise["precision"]))
