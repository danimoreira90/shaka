"""Configuration knobs for shaka.

Design knobs (not domain facts) live here: chunking, embedding dimension,
backend default, cost caps. Sprint 0 only needs chunking. Values are
character-based for the plain-text Sprint 0 slice.
"""

# Chunking (character-based for Sprint 0; revisit for token-based later).
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
