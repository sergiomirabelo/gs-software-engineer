import logging
import re
import time

from src.domain.errors import InvalidQuestion, StopNotFound
from src.domain.models import Answer, Stop, StopStatus
from src.domain.ports import AssistantPort, StopRepository

logger = logging.getLogger("citizentech.domain")

MAX_QUESTION_LEN = 500
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Guardrail de saída: CPF, e-mail e celular não podem sair na resposta.
_PII = re.compile(
    r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}"
    r"|[\w.+-]+@[\w-]+\.[\w.-]+"
    r"|\(?\d{2}\)?\s?9\d{4}-?\d{4}"
)

REFUSAL_NO_CONTEXT = (
    "Não encontrei esse ponto na base oficial, então não vou inventar uma resposta. "
    "Informe o código (ex.: pt-001) ou o nome exato do ponto."
)
REFUSAL_PII = "Não posso exibir dados pessoais. Reformule a pergunta sobre o ponto ou a linha."


def sanitize_question(raw: str) -> str:
    cleaned = _CONTROL_CHARS.sub("", raw).strip()
    if not cleaned:
        raise InvalidQuestion("A pergunta está vazia após sanitização")
    if len(cleaned) > MAX_QUESTION_LEN:
        raise InvalidQuestion(f"A pergunta excede {MAX_QUESTION_LEN} caracteres")
    return cleaned


class StopService:
    def __init__(self, repo: StopRepository):
        self._repo = repo

    def get(self, stop_id: str) -> Stop:
        stop = self._repo.get(stop_id)
        if stop is None:
            raise StopNotFound(stop_id)
        return stop

    def list(
        self, *, status: StopStatus | None, limit: int, offset: int
    ) -> tuple[list[Stop], int]:
        return self._repo.list(status=status, limit=limit, offset=offset)


class AskService:
    def __init__(self, repo: StopRepository, assistant: AssistantPort):
        self._repo = repo
        self._assistant = assistant

    def ask(self, question: str, stop_id: str | None = None) -> Answer:
        started = time.perf_counter()
        question = sanitize_question(question)

        if stop_id is not None:
            stop = self._repo.get(stop_id)
            if stop is None:
                raise StopNotFound(stop_id)
        else:
            stop = self._repo.find_in_text(question)

        # Guardrail 1: sem dado na base, a IA nem é chamada (não inventa).
        if stop is None:
            self._log(None, True, "no_context", started)
            return Answer(REFUSAL_NO_CONTEXT, None, True)

        alternative = (
            self._repo.get(stop.alternative_stop_id) if stop.alternative_stop_id else None
        )
        text = self._assistant.answer(question, stop, alternative)

        # Guardrail 2: dado pessoal na saída => bloqueia.
        if _PII.search(text):
            self._log(stop.id, True, "pii_blocked", started)
            return Answer(REFUSAL_PII, stop.id, True)

        self._log(stop.id, False, "ok", started)
        return Answer(text, stop.id, False)

    @staticmethod
    def _log(stop_id: str | None, refused: bool, reason: str, started: float) -> None:
        logger.info(
            "ask stop=%s refused=%s reason=%s latency_ms=%.1f",
            stop_id, refused, reason, (time.perf_counter() - started) * 1000,
        )
