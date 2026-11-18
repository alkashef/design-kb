"""OllamaEmbedder: the only module that calls Ollama (D-16)."""

import json
import logging
import urllib.error
import urllib.request
from typing import List, Optional

from src.domain.models import EmbeddingUnavailable

logger = logging.getLogger(__name__)

EMBED_PATH = "/api/embed"
SIZE_PROBE_TEXT = "vector size probe"


class OllamaEmbedder:
    """Turns texts into vectors with the embedding model that Ollama runs."""

    def __init__(self, url: str, model: str, timeout_seconds: float):
        """Keep the address of Ollama, the model name and the longest time to wait."""
        self._url = url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._vector_size: Optional[int] = None

    @property
    def model_name(self) -> str:
        """Return the name of the embedding model."""
        return self._model

    @property
    def vector_size(self) -> int:
        """Return the length of each vector; the first time, embed a probe text to learn it."""
        if self._vector_size is None:
            self.embed([SIZE_PROBE_TEXT])
        return self._vector_size

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return one vector for each text, or raise EmbeddingUnavailable."""
        if not texts:
            return []
        embeddings = self._post({"model": self._model, "input": texts}).get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts) or not embeddings[0]:
            logger.warning("Ollama answered with no usable embeddings.")
            raise EmbeddingUnavailable("The embedding model gave no usable answer.")
        self._vector_size = len(embeddings[0])
        return embeddings

    def _post(self, body: dict) -> dict:
        """Send body to POST <url>/api/embed and return the JSON answer."""
        request = urllib.request.Request(
            self._url + EMBED_PATH,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            logger.warning(
                "Ollama answered with HTTP status %s; the model may not be pulled.", error.code
            )
            raise EmbeddingUnavailable("The embedding model does not answer.") from error
        except (OSError, ValueError) as error:
            logger.warning("Ollama did not answer: %s", type(error).__name__)
            raise EmbeddingUnavailable("The embedding model does not answer.") from error
