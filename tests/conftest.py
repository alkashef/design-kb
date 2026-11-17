"""Shared fixtures of the route tests (docs/design.md, Test policy)."""

import pytest
from fastapi.testclient import TestClient

from fakes import FakeEmbedder
from src.adapters.store import LanceStore
from src.app import AppOptions, create_app

TEST_SEARCH_RESULT_LIMIT = 10
TEST_PAGE_SIZE = 10


@pytest.fixture
def store(tmp_path):
    """A LanceStore in a temporary folder."""
    return LanceStore(str(tmp_path / "data"))


@pytest.fixture
def embedder():
    """A FakeEmbedder that answers every call."""
    return FakeEmbedder()


def _client_for(store, embedder, load_seed):
    """Return the test client of the app built with the given store, embedder and seed option."""
    options = AppOptions(
        search_result_limit=TEST_SEARCH_RESULT_LIMIT,
        page_size=TEST_PAGE_SIZE,
        load_seed=load_seed,
    )
    return TestClient(create_app(store, embedder, options))


@pytest.fixture
def client(store, embedder):
    """The test client of the app with an empty store and no seed data."""
    with _client_for(store, embedder, load_seed=False) as test_client:
        yield test_client


@pytest.fixture
def seeded_client(store, embedder):
    """The test client of the app that loads the seed data into the empty store."""
    with _client_for(store, embedder, load_seed=True) as test_client:
        yield test_client
