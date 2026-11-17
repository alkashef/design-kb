"""OllamaEmbedder: the only module that calls Ollama (D-16). M10 completes it."""


class OllamaEmbedder:
    """Turns texts into vectors with the embedding model that Ollama runs."""

    def __init__(self, url: str, model: str, timeout_seconds: float):
        """Keep the address of Ollama, the model name and the longest time to wait."""
        self._url = url
        self._model = model
        self._timeout_seconds = timeout_seconds

    @property
    def model_name(self) -> str:
        """Return the name of the embedding model."""
        return self._model

    @property
    def vector_size(self) -> int:
        """Return the length of each vector. M10 builds it."""
        raise NotImplementedError("The embedder is completed in milestone M10.")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector for each text. M10 builds it."""
        raise NotImplementedError("The embedder is completed in milestone M10.")
