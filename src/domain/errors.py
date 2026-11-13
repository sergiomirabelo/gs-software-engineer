class DomainError(Exception):
    """Base de erros de negócio."""


class StopNotFound(DomainError):
    def __init__(self, stop_id: str):
        super().__init__(f"Ponto '{stop_id}' não encontrado")
        self.stop_id = stop_id


class InvalidQuestion(DomainError):
    """Pergunta vazia ou inválida após sanitização."""


class AssistantUnavailable(DomainError):
    """O provedor de IA está fora do ar ou excedeu o timeout."""
