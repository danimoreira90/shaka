"""Domain models for shaka (Task 0.1).

Pure data: pydantic v2 models with validation and the `doc_id` hash only.
No I/O, no AWS, no orchestration — see KICKOFF.md module map (HR-8).

Canonical names follow CONTEXT.md: Document, Chunk, Embedding, Query,
Answer, Citation.
"""

import hashlib

from pydantic import BaseModel, computed_field, model_validator


class Citation(BaseModel):
    """A pointer from an Answer back to the Chunk that supports it (HR-5).

    `position` is the supporting Chunk's location in its parent Document
    (page or character offset); `snippet` is the cited text.
    """

    doc_id: str
    position: int
    snippet: str


class Document(BaseModel):
    """One paper, article, or book the user owns — the unit of input.

    `doc_id` is a stable SHA-256 of the extracted `text`: same text yields
    the same id (idempotent ingestion), independent of `source`.
    """

    source: str
    text: str
    metadata: dict[str, str] = {}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def doc_id(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


class Chunk(BaseModel):
    """A slice of a Document's text, small enough to embed and retrieve.

    Carries its parent `doc_id` and `position` so an Answer can cite it.
    """

    doc_id: str
    position: int
    text: str


class Embedding(BaseModel):
    """A vector representing a Chunk's meaning (the vector, not the model)."""

    vector: list[float]


class Query(BaseModel):
    """A user question entering the query path."""

    text: str


class Answer(BaseModel):
    """The grounded reply plus its Citations.

    HR-5(b): a found answer makes a factual claim and must cite at least
    one Chunk. A not-found answer ("not in your library") carries none.
    """

    found: bool
    text: str
    citations: list[Citation]

    @model_validator(mode="after")
    def _grounded_answer_requires_citation(self) -> "Answer":
        if self.found and not self.citations:
            raise ValueError("a grounded answer (found=True) requires >=1 citation (HR-5)")
        return self
