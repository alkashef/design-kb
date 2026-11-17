"""Start design-kb: read the settings, create the store and the embedder, and run the server."""

import logging

import uvicorn

from src.adapters.embedder import OllamaEmbedder
from src.adapters.store import LanceStore
from src.app import AppOptions, create_app
from src.config import load_settings


def main() -> None:
    """Build the app from the settings and serve it with Uvicorn."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    store = LanceStore(settings.data_dir)
    embedder = OllamaEmbedder(
        settings.ollama_url, settings.embedding_model, settings.embedding_timeout_seconds
    )
    options = AppOptions(
        search_result_limit=settings.search_result_limit,
        page_size=settings.page_size,
        load_seed=True,
    )
    uvicorn.run(create_app(store, embedder, options), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
