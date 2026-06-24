"""Local chunker (Task 0.3): free, deterministic, no AWS.

Satisfies the Chunker port by sliding a fixed-size character window over
the text with a fixed overlap. Each Chunk records its parent doc_id and
its character-offset position so an Answer can later cite it.
"""

from shaka.config import CHUNK_OVERLAP, CHUNK_SIZE
from shaka.domain.models import Chunk


class LocalChunker:
    """Splits text into overlapping character windows.

    Defaults come from shaka.config; tests may pass explicit values.
    """

    def __init__(self, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> None:
        if size <= 0:
            raise ValueError("chunk size must be positive")
        if not 0 <= overlap < size:
            raise ValueError("chunk overlap must be >=0 and < size")
        self.size = size
        self.overlap = overlap

    def chunk(self, text: str, doc_id: str) -> list[Chunk]:
        if not text:
            return []

        step = self.size - self.overlap
        chunks: list[Chunk] = []
        start = 0
        while start < len(text):
            piece = text[start : start + self.size]
            chunks.append(Chunk(doc_id=doc_id, position=start, text=piece))
            if start + self.size >= len(text):
                break
            start += step
        return chunks
