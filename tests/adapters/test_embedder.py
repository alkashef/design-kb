"""Tests of OllamaEmbedder against a fake HTTP server (docs/design.md, D-16, D-27, D-42)."""

import logging
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from src.adapters.embedder import OllamaEmbedder
from src.domain.models import EmbeddingUnavailable

TIMEOUT_SECONDS = 5
MODEL = "invented-model"


class _ErrorHandler(BaseHTTPRequestHandler):
    """Answers every POST with status 404."""

    def do_POST(self):
        """Read the body and answer 404."""
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        """Keep the test output quiet."""


@pytest.fixture
def error_server_url():
    """A server on 127.0.0.1 that answers 404; yields its address."""
    server = HTTPServer(("127.0.0.1", 0), _ErrorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def closed_url():
    """An address on 127.0.0.1 where nothing listens."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}"


def _embed(url):
    return OllamaEmbedder(url, MODEL, TIMEOUT_SECONDS).embed(["alpha beta"])


def test_embedder_http_error_log_names_status_and_model_hint(error_server_url, caplog):
    caplog.set_level(logging.DEBUG)
    with pytest.raises(EmbeddingUnavailable):
        _embed(error_server_url)
    text = " ".join(r.getMessage() for r in caplog.records).lower()
    assert "404" in text
    assert "pulled" in text or "model" in text and "missing" in text
    assert "alpha beta" not in text


def test_embedder_http_error_raises_embedding_unavailable(error_server_url):
    with pytest.raises(EmbeddingUnavailable):
        _embed(error_server_url)


def test_embedder_connection_error_keeps_did_not_answer_log(closed_url, caplog):
    caplog.set_level(logging.DEBUG)
    with pytest.raises(EmbeddingUnavailable):
        _embed(closed_url)
    text = " ".join(r.getMessage() for r in caplog.records)
    assert "Ollama did not answer" in text
