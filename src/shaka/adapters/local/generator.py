"""Local generator (Task 0.6): deterministic, grounded, no FM.

The free local stand-in for the Bedrock generator (the Generator port).
It never invents content: with no retrieved chunks it returns a not-found
Answer; otherwise it grounds the Answer on the top chunk and cites it.
HR-5 is enforced by construction — a found Answer always carries a Citation.
"""

from shaka.domain.models import Answer, Chunk, Citation

# Longest snippet (chars) lifted from the top chunk into the citation.
_SNIPPET_LEN = 200

_NOT_FOUND_TEXT = "That is not in your library."


class LocalGenerator:
    """Deterministic grounded generator satisfying the Generator port."""

    def generate(self, question: str, chunks: list[Chunk]) -> Answer:
        if not chunks:
            return Answer(found=False, text=_NOT_FOUND_TEXT, citations=[])

        top = chunks[0]
        snippet = top.text[:_SNIPPET_LEN]
        citation = Citation(doc_id=top.doc_id, position=top.position, snippet=snippet)
        text = f"Based on your library: {snippet}"
        return Answer(found=True, text=text, citations=[citation])
