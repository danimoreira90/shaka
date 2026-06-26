"""Local generator grounding (Task 0.6).

The deterministic local stand-in for the Bedrock generator. It enforces
the HR-5 contract by construction: no chunks -> not-found answer; chunks
-> a grounded answer that cites the top chunk.
"""

from shaka.adapters.local.generator import LocalGenerator
from shaka.domain.models import Answer, Chunk


def test_empty_chunks_returns_not_found_answer() -> None:
    generator = LocalGenerator()

    answer = generator.generate("what is alpha?", [])

    assert isinstance(answer, Answer)
    assert answer.found is False
    assert answer.citations == []
    assert "not in your library" in answer.text.lower()


def test_non_empty_chunks_returns_grounded_answer_citing_top_chunk() -> None:
    generator = LocalGenerator()
    top = Chunk(doc_id="doc-1", position=7, text="alpha beta gamma")
    other = Chunk(doc_id="doc-1", position=42, text="unrelated tail")

    answer = generator.generate("what is alpha?", [top, other])

    assert answer.found is True
    assert len(answer.citations) >= 1
    # The citation points at the top (first) chunk.
    assert answer.citations[0].doc_id == top.doc_id
    assert answer.citations[0].position == top.position


def test_grounded_answer_satisfies_hr5_contract() -> None:
    generator = LocalGenerator()
    top = Chunk(doc_id="doc-1", position=0, text="alpha beta gamma")

    # If HR-5 were violated (found=True, empty citations), construction would raise.
    answer = generator.generate("what is alpha?", [top])

    assert answer.found is True
    assert answer.citations  # non-empty
