"""Portas (interfaces). O domínio só conhece estes contratos."""
from typing import Protocol

from src.domain.models import Stop, StopStatus


class StopRepository(Protocol):
    def get(self, stop_id: str) -> Stop | None: ...

    def list(
        self, *, status: StopStatus | None, limit: int, offset: int
    ) -> tuple[list[Stop], int]:
        """Retorna (itens da página, total após filtro)."""
        ...

    def find_in_text(self, text: str) -> Stop | None: ...


class AssistantPort(Protocol):
    def answer(self, question: str, stop: Stop, alternative: Stop | None) -> str:
        """Gera resposta ancorada SOMENTE nos dados recebidos.

        Deve levantar AssistantUnavailable se o provedor falhar.
        """
        ...
