"""Local vector index (Task 0.5): in-memory, free, no AWS.

Holds (Chunk, Embedding) pairs and answers nearest-k queries by cosine
similarity, highest first. Cosine is computed by hand with stdlib math —
no numpy — and the zero-vector case yields similarity 0 (no division).
"""

import math

from shaka.domain.models import Chunk, Embedding


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class LocalVectorIndex:
    """In-memory VectorIndex satisfying the VectorIndex port."""

    def __init__(self) -> None:
        self._entries: list[tuple[Chunk, Embedding]] = []

    def add(self, chunk: Chunk, embedding: Embedding) -> None:
        self._entries.append((chunk, embedding))

    def search(self, query_embedding: Embedding, k: int) -> list[Chunk]:
        scored = [
            (_cosine(query_embedding.vector, embedding.vector), chunk)
            for chunk, embedding in self._entries
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]
