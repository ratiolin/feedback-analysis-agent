import numpy as np
import pytest

from feedback_app.embeddings import blended_embeddings


class FakeEmbedder:
    def encode(self, texts: list[str]) -> np.ndarray:
        mapping = {
            "raw-a": [1.0, 0.0],
            "raw-b": [0.0, 1.0],
            "summary-a": [1.0, 0.0],
            "summary-b": [1.0, 0.0],
        }
        return np.asarray([mapping[text] for text in texts], dtype=float)


def test_blended_embeddings_preserve_weighted_cosine_contract() -> None:
    vectors = blended_embeddings(
        FakeEmbedder(),
        ["raw-a", "raw-b"],
        ["summary-a", "summary-b"],
        raw_weight=0.8,
    )
    assert np.isclose(vectors[0] @ vectors[1], 0.2)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1)


def test_blended_embeddings_reject_invalid_contract() -> None:
    with pytest.raises(ValueError, match="equal length"):
        blended_embeddings(FakeEmbedder(), ["raw-a"], [], 0.8)
    with pytest.raises(ValueError, match="between"):
        blended_embeddings(FakeEmbedder(), ["raw-a"], ["summary-a"], 1.1)
