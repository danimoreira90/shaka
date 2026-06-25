"""Local vector index behaviour (Task 0.5).

In-memory store of (Chunk, Embedding) pairs; search returns the k nearest
chunks by cosine similarity, highest first. Hand-crafted orthogonal-ish
vectors keep the ranking deterministic and easy to reason about.
"""

from shaka.adapters.local.vector_index import LocalVectorIndex
from shaka.domain.models import Chunk, Embedding

CHUNK_A = Chunk(doc_id="d", position=0, text="alpha")
CHUNK_B = Chunk(doc_id="d", position=1, text="beta")
CHUNK_C = Chunk(doc_id="d", position=2, text="gamma")

EMB_A = Embedding(vector=[1.0, 0.0, 0.0])
EMB_B = Embedding(vector=[0.0, 1.0, 0.0])
EMB_C = Embedding(vector=[0.0, 0.0, 1.0])


def _seeded_index() -> LocalVectorIndex:
    index = LocalVectorIndex()
    index.add(CHUNK_A, EMB_A)
    index.add(CHUNK_B, EMB_B)
    index.add(CHUNK_C, EMB_C)
    return index


def test_query_closest_to_a_chunk_returns_it_first() -> None:
    index = _seeded_index()

    # Query leans heavily toward EMB_A.
    results = index.search(Embedding(vector=[0.9, 0.1, 0.0]), k=3)

    assert results[0] == CHUNK_A


def test_search_respects_k() -> None:
    index = _seeded_index()

    results = index.search(Embedding(vector=[0.9, 0.1, 0.0]), k=2)

    assert len(results) == 2


def test_empty_index_returns_empty_list() -> None:
    index = LocalVectorIndex()

    assert index.search(Embedding(vector=[1.0, 0.0, 0.0]), k=3) == []


def test_ranking_is_by_cosine_similarity() -> None:
    index = _seeded_index()

    # Query identical to EMB_A must rank CHUNK_A top, ahead of the dissimilar ones.
    results = index.search(Embedding(vector=[1.0, 0.0, 0.0]), k=3)

    assert results[0] == CHUNK_A
    assert CHUNK_B in results and CHUNK_C in results
