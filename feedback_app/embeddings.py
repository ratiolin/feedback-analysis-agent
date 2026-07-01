from typing import Protocol

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class TfidfEmbedder:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), min_df=1)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.vectorizer.fit_transform(texts).toarray()


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("install the 'embedding' extra to use BGE embeddings") from exc
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )
