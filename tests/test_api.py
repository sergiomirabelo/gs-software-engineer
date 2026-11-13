"""Testes de API: feliz, erros (400/404/422/503) e paginação. Sem LLM real."""
from tests.fakes import DownAssistant


def test_get_stop_ok(client):  # caminho feliz
    r = client.get("/stops/pt-003")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "SUSPENDED"
    assert body["alternative_stop_id"] == "pt-004"


def test_get_stop_not_found_returns_standard_error(client):  # caminho de erro
    r = client.get("/stops/nao-existe")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert r.json()["details"] == []


def test_list_stops_pagination_and_filter(client):
    page1 = client.get("/stops", params={"limit": 3}).json()
    assert len(page1["items"]) == 3 and page1["next_offset"] == 3
    last = client.get("/stops", params={"limit": 3, "offset": 6}).json()
    assert last["next_offset"] is None
    delayed = client.get("/stops", params={"status": "DELAYED"}).json()
    assert delayed["total"] == 2


def test_list_stops_invalid_limit_returns_400(client):
    r = client.get("/stops", params={"limit": 0})
    assert r.status_code == 400
    assert r.json()["code"] == "BAD_REQUEST"


def test_list_stops_invalid_status_returns_400(client):
    assert client.get("/stops", params={"status": "VOANDO"}).status_code == 400


def test_ask_with_stop_id_uses_assistant(client, spy):
    r = client.post("/ask", json={"question": "Posso esperar aqui?", "stop_id": "pt-002"})
    assert r.status_code == 200
    assert r.json() == {"answer": "resposta fake", "stop_id": "pt-002", "refused": False}
    assert len(spy.calls) == 1


def test_ask_empty_question_returns_422(client):
    r = client.post("/ask", json={"question": ""})
    assert r.status_code == 422
    assert r.json()["code"] == "UNPROCESSABLE_ENTITY"


def test_ask_unknown_stop_id_returns_404(client):
    r = client.post("/ask", json={"question": "Como está?", "stop_id": "xx"})
    assert r.status_code == 404


def test_ask_when_llm_down_returns_503(make_client):
    r = make_client(DownAssistant()).post(
        "/ask", json={"question": "Como está?", "stop_id": "pt-001"}
    )
    assert r.status_code == 503
    assert r.json()["code"] == "SERVICE_UNAVAILABLE"


def test_unknown_route_uses_standard_error(client):
    r = client.get("/nada")
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"
