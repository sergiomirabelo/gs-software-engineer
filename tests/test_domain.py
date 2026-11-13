"""Testes do domínio e dos guardrails com fake (sem framework web, sem LLM)."""
import pytest

from src.domain.errors import AssistantUnavailable, InvalidQuestion
from src.domain.services import (
    REFUSAL_NO_CONTEXT,
    REFUSAL_PII,
    AskService,
    sanitize_question,
)
from tests.fakes import DownAssistant, SpyAssistant


def test_guardrail_no_context_refuses_without_calling_llm(repo):
    spy = SpyAssistant()
    answer = AskService(repo, spy).ask("Qual o horário do metrô de Paris?")
    assert answer.refused is True
    assert answer.text == REFUSAL_NO_CONTEXT
    assert spy.calls == []  # a IA nem foi chamada


def test_stop_found_by_name_ignoring_accents(repo):
    spy = SpyAssistant()
    answer = AskService(repo, spy).ask("como esta a praca da se hoje?")
    assert answer.stop_id == "pt-003" and answer.refused is False


def test_alternative_is_passed_to_assistant(repo):
    spy = SpyAssistant()
    AskService(repo, spy).ask("e agora?", stop_id="pt-003")
    _, stop, alternative = spy.calls[0]
    assert stop.id == "pt-003" and alternative.id == "pt-004"


@pytest.mark.parametrize(
    "leak", ["fale com maria@email.com", "CPF 123.456.789-09", "ligue (11) 91234-5678"]
)
def test_guardrail_blocks_personal_data_in_output(repo, leak):
    answer = AskService(repo, SpyAssistant(reply=leak)).ask("status?", stop_id="pt-001")
    assert answer.refused is True and answer.text == REFUSAL_PII


def test_sanitize_removes_control_chars_and_rejects_empty():
    assert sanitize_question("  oi\x00 ponto\x07  ") == "oi ponto"
    with pytest.raises(InvalidQuestion):
        sanitize_question("\x00\x01  ")
    with pytest.raises(InvalidQuestion):
        sanitize_question("a" * 501)


def test_assistant_failure_propagates_as_domain_error(repo):
    with pytest.raises(AssistantUnavailable):
        AskService(repo, DownAssistant()).ask("status?", stop_id="pt-001")
