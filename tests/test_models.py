"""Domain model invariants (Task 0.1).

Covers the four RED cases from PLAN.md Task 0.1, including the HR-5
citation contract: a grounded answer must carry at least one Citation.
"""

import pytest
from pydantic import ValidationError

from shaka.domain.models import Answer, Citation, Document


def test_citation_constructs() -> None:
    citation = Citation(doc_id="abc123", position=0, snippet="a slice of text")

    assert citation.doc_id == "abc123"
    assert citation.position == 0
    assert citation.snippet == "a slice of text"


def test_grounded_answer_without_citations_raises() -> None:
    # HR-5: a found answer makes a factual claim and so needs >=1 citation.
    with pytest.raises(ValidationError):
        Answer(found=True, text="x", citations=[])


def test_not_found_answer_without_citations_is_valid() -> None:
    answer = Answer(found=False, text="not in your library", citations=[])

    assert answer.found is False
    assert answer.citations == []


def test_document_doc_id_is_a_stable_hash_of_text() -> None:
    doc_a = Document(source="paper.txt", text="the same text")
    doc_b = Document(source="other-name.txt", text="the same text")
    doc_c = Document(source="paper.txt", text="different text")

    # Same text -> same doc_id (independent of source).
    assert doc_a.doc_id == doc_b.doc_id
    # Different text -> different doc_id.
    assert doc_a.doc_id != doc_c.doc_id
