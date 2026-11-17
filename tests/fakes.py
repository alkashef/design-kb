"""Fakes for the tests: an embedder that needs no Ollama (docs/design.md, Test policy)."""

import math
import zlib

from src.domain.models import EmbeddingUnavailable

FAKE_VECTOR_SIZE = 64
FAKE_MODEL_NAME = "fake-embedding"


class FakeEmbedder:
    """Turns texts into deterministic word-count vectors and records every call."""

    def __init__(self, available: bool = True):
        """Make the fake. With available=False, each call raises EmbeddingUnavailable."""
        self.available = available
        self.calls: list[list[str]] = []

    @property
    def model_name(self) -> str:
        """Return the name of the fake model."""
        return FAKE_MODEL_NAME

    @property
    def vector_size(self) -> int:
        """Return the length of each vector."""
        return FAKE_VECTOR_SIZE

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector of length 1 for each text, or raise when the fake is unavailable."""
        if not self.available:
            raise EmbeddingUnavailable("The fake embedding model is unavailable.")
        self.calls.append(list(texts))
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        """Add 1 at the crc32 position of each lower-case word, then scale to length 1."""
        vector = [0.0] * FAKE_VECTOR_SIZE
        for word in text.lower().split():
            vector[zlib.crc32(word.encode("utf-8")) % FAKE_VECTOR_SIZE] += 1.0
        length = math.sqrt(sum(value * value for value in vector))
        if length == 0:
            return vector
        return [value / length for value in vector]
