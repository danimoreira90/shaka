"""Local embedder (Task 0.4): deterministic bag-of-words feature hash.

Free, no AWS, no model. Lowercases, splits on whitespace, hashes each
token into a fixed bucket and accumulates counts into a float vector of
length config.EMBED_DIM. Uses hashlib (not Python's salted hash()) so
vectors are stable across runs — the property retrieval depends on.
"""

import hashlib

from shaka.config import EMBED_DIM
from shaka.domain.models import Embedding


class LocalEmbedder:
    """Bag-of-words feature-hash embedder satisfying the Embedder port."""

    def __init__(self, dim: int = EMBED_DIM) -> None:
        if dim <= 0:
            raise ValueError("embedding dimension must be positive")
        self.dim = dim

    def _bucket(self, token: str) -> int:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.dim

    def embed(self, text: str) -> Embedding:
        vector = [0.0] * self.dim
        for token in text.lower().split():
            vector[self._bucket(token)] += 1.0
        return Embedding(vector=vector)
