"""Turns a rejected entry or an unavailable embedding model into the message and the status of the
page that a route shows (D-27, D-29)."""

import logging
from typing import Tuple

from src.domain.models import EmbeddingUnavailable

logger = logging.getLogger(__name__)

REJECTED_STATUS = 422
UNAVAILABLE_STATUS = 503
MODEL_UNAVAILABLE_MESSAGE = (
    "The embedding model does not answer, so nothing was saved. Start Ollama and try again."
)
SEARCH_UNAVAILABLE_MESSAGE = (
    "The embedding model does not answer, so the search cannot run. Start Ollama and try again."
)


def failure_of(error: Exception) -> Tuple[str, int]:
    """Return the message and the status for error; log an unavailable model."""
    if isinstance(error, EmbeddingUnavailable):
        logger.warning("The embedding model does not answer; the entry was not saved.")
        return MODEL_UNAVAILABLE_MESSAGE, UNAVAILABLE_STATUS
    return str(error), REJECTED_STATUS


def search_failure() -> Tuple[str, int]:
    """Return the message and the status of a search that cannot run; log it (D-27)."""
    logger.warning("The embedding model does not answer; the search did not run.")
    return SEARCH_UNAVAILABLE_MESSAGE, UNAVAILABLE_STATUS
