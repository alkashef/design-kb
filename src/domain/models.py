"""The data classes and errors of the domain (docs/design.md, Interfaces)."""


class EmbeddingUnavailable(Exception):
    """Raised by an embedder when the embedding model does not answer (D-27)."""
