from src.domain.errors import AssistantUnavailable
from src.domain.models import Stop


class SpyAssistant:
    """Fake determinístico: registra chamadas e devolve texto fixo. Nunca toca em LLM real."""

    def __init__(self, reply: str = "resposta fake"):
        self.reply = reply
        self.calls: list[tuple[str, Stop, Stop | None]] = []

    def answer(self, question: str, stop: Stop, alternative: Stop | None) -> str:
        self.calls.append((question, stop, alternative))
        return self.reply


class DownAssistant:
    def answer(self, question: str, stop: Stop, alternative: Stop | None) -> str:
        raise AssistantUnavailable("timeout simulado")
