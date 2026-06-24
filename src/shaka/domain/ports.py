"""Domain ports for shaka (Task 0.2).

The doors the app talks to (HR-8): `domain/` and `app/` depend on these
Protocols, never on AWS. Each port gets a `local` fake and an `aws` adapter
in later tasks. Interfaces only — no implementations here.

Canonical names follow CONTEXT.md.
"""

from typing import Protocol, runtime_checkable

from shaka.domain.models import Answer, Chunk, Embedding


@runtime_checkable
class Chunker(Protocol):
    """text -> chunks. Splits a Document's text into retrievable slices."""

    def chunk(self, text: str, doc_id: str) -> list[Chunk]: ...


@runtime_checkable
class Embedder(Protocol):
    """chunk text -> vector. Produces an Embedding for a piece of text."""

    def embed(self, text: str) -> Embedding: ...


@runtime_checkable
class VectorIndex(Protocol):
    """Stores (chunk, embedding) pairs and answers nearest-k queries."""

    def add(self, chunk: Chunk, embedding: Embedding) -> None: ...

    def search(self, query_embedding: Embedding, k: int) -> list[Chunk]: ...


@runtime_checkable
class Generator(Protocol):
    """question + retrieved chunks -> grounded Answer (HR-5)."""

    def generate(self, question: str, chunks: list[Chunk]) -> Answer: ...
