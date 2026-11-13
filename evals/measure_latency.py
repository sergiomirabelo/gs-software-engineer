"""Mede p95 local (TestClient, provedor fake). Mede o overhead do serviço, NÃO o de um LLM real."""
import statistics
import time

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.domain.services import AskService, StopService
from src.infra.assistants import TemplateAssistant
from src.infra.repository import InMemoryStopRepository
from src.infra.seed import SEED_STOPS


def p95(samples: list[float]) -> float:
    return statistics.quantiles(samples, n=100)[94]


def measure(call, n: int = 300) -> float:
    call()  # aquecimento
    samples = []
    for _ in range(n):
        t = time.perf_counter()
        call()
        samples.append((time.perf_counter() - t) * 1000)
    return p95(samples)


repo = InMemoryStopRepository(SEED_STOPS)
client = TestClient(create_app(StopService(repo), AskService(repo, TemplateAssistant())))
body = {"question": "Como está?", "stop_id": "pt-003"}
get_p95 = measure(lambda: client.get("/stops/pt-003"))
ask_p95 = measure(lambda: client.post("/ask", json=body))
print(f"p95 GET /stops/pt-003 = {get_p95:.1f} ms (meta < 300)")
print(f"p95 POST /ask        = {ask_p95:.1f} ms (meta < 4000)")
