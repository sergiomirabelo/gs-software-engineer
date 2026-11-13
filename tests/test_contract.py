"""Testes de contrato: o código responde exatamente o que o YAML promete."""
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate

from src.domain.models import StopStatus

SPEC_PATH = Path(__file__).resolve().parent.parent / "openapi" / "2_contrato_api.yaml"
SPEC = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def assert_matches(schema_name: str, instance) -> None:
    schema = {"$ref": f"#/components/schemas/{schema_name}", "components": SPEC["components"]}
    Draft202012Validator(schema).validate(instance)


def test_spec_is_valid_openapi():
    validate(SPEC)


def test_all_contract_operations_exist_in_code(client):
    code_paths = client.app.openapi()["paths"]
    for path, methods in SPEC["paths"].items():
        for method in methods:
            assert method in code_paths.get(path, {}), f"{method.upper()} {path} sem implementação"


def test_status_enum_in_yaml_equals_domain_enum():
    assert set(SPEC["components"]["schemas"]["StopStatus"]["enum"]) == {s.value for s in StopStatus}


@pytest.mark.parametrize("stop_id", ["pt-001", "pt-003", "pt-007"])
def test_get_stop_response_matches_schema(client, stop_id):
    assert_matches("Stop", client.get(f"/stops/{stop_id}").json())


def test_list_response_matches_schema(client):
    assert_matches("StopPage", client.get("/stops").json())


def test_ask_response_matches_schema(client):
    ok = client.post("/ask", json={"question": "Como está?", "stop_id": "pt-001"}).json()
    refused = client.post("/ask", json={"question": "Previsão do tempo em Marte"}).json()
    assert_matches("AskResponse", ok)
    assert_matches("AskResponse", refused)
    assert refused["refused"] is True


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.get("/stops/xx"),
        lambda c: c.get("/stops", params={"limit": 999}),
        lambda c: c.post("/ask", json={"question": ""}),
    ],
)
def test_error_bodies_match_error_schema(client, call):
    response = call(client)
    assert response.status_code in (400, 404, 422)
    assert_matches("Error", response.json())
