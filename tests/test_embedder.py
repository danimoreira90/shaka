"""Local embedder behaviour (Task 0.4).

A deterministic bag-of-words feature-hash embedder: no AWS, no model,
stable across runs. The cosine property is what makes retrieval work —
texts sharing words must sit closer than texts sharing none.
"""

import math

from shaka.adapters.local.embedder import LocalEmbedder
from shaka.config import EMBED_DIM
from shaka.domain.models import Embedding


def _cosine(a: Embedding, b: Embedding) -> float:
    dot = sum(x * y for x, y in zip(a.vector, b.vector))
    norm_a = math.sqrt(sum(x * x for x in a.vector))
    norm_b = math.sqrt(sum(y * y for y in b.vector))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def test_same_text_gives_identical_vector() -> None:
    embedder = LocalEmbedder()

    assert embedder.embed("hello world").vector == embedder.embed("hello world").vector


def test_different_text_gives_different_vector() -> None:
    embedder = LocalEmbedder()

    assert embedder.embed("hello world").vector != embedder.embed("goodbye moon").vector


def test_vector_length_equals_embed_dim() -> None:
    embedder = LocalEmbedder()

    assert len(embedder.embed("anything at all").vector) == EMBED_DIM


def test_shared_words_score_higher_cosine_than_no_shared_words() -> None:
    embedder = LocalEmbedder()

    base = embedder.embed("machine learning models train on data")
    related = embedder.embed("machine learning models learn from data")
    unrelated = embedder.embed("the quick brown fox jumps high")

    assert _cosine(base, related) > _cosine(base, unrelated)
