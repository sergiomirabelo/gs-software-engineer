import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.domain.services import AskService, StopService
from src.infra.repository import InMemoryStopRepository
from src.infra.seed import SEED_STOPS
from tests.fakes import SpyAssistant


@pytest.fixture
def repo():
    return InMemoryStopRepository(SEED_STOPS)


@pytest.fixture
def spy():
    return SpyAssistant()


@pytest.fixture
def make_client(repo):
    def _make(assistant):
        app = create_app(StopService(repo), AskService(repo, assistant))
        return TestClient(app)

    return _make


@pytest.fixture
def client(make_client, spy):
    return make_client(spy)
