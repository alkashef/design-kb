"""Log each request of the app with its method, path, status and time (CLAUDE.md, Code quality)."""

import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)


async def log_request(request: Request, call_next):
    """Log one request and its answer. Log an error with its context, then raise it again.

    The log holds the path but not the query string, so it never holds user data.
    """
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("%s %s failed", request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %d %.1f ms", request.method, request.url.path, response.status_code, elapsed_ms
    )
    return response
