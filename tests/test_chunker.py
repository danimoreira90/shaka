"""Local chunker behaviour (Task 0.3).

The Chunker splits a Document's text into overlapping, retrievable Chunks.
Tests pass explicit size/overlap so chunk counts are deterministic;
production defaults live in shaka.config.
"""

from shaka.adapters.local.chunker import LocalChunker
from shaka.domain.models import Chunk

# 20 chars: indices 0..19
TEXT = "abcdefghijklmnopqrst"


def test_known_text_produces_expected_chunk_count() -> None:
    # size=10, overlap=3 -> step=7 -> starts at 0, 7, 14 -> 3 chunks.
    chunker = LocalChunker(size=10, overlap=3)

    chunks = chunker.chunk(TEXT, doc_id="doc1")

    assert len(chunks) == 3
    assert [c.text for c in chunks] == ["abcdefghij", "hijklmnopq", "opqrst"]


def test_consecutive_chunks_overlap() -> None:
    overlap = 3
    chunker = LocalChunker(size=10, overlap=overlap)

    chunks = chunker.chunk(TEXT, doc_id="doc1")

    for current, nxt in zip(chunks, chunks[1:]):
        # The tail of chunk n is the head of chunk n+1.
        assert current.text[-overlap:] == nxt.text[:overlap]


def test_each_chunk_carries_doc_id_and_position() -> None:
    chunker = LocalChunker(size=10, overlap=3)

    chunks = chunker.chunk(TEXT, doc_id="doc-xyz")

    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.doc_id == "doc-xyz" for c in chunks)
    # position is the character offset of each chunk's start.
    assert [c.position for c in chunks] == [0, 7, 14]


def test_empty_text_produces_no_chunks() -> None:
    chunker = LocalChunker(size=10, overlap=3)

    assert chunker.chunk("", doc_id="doc1") == []
