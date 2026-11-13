import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Trocar de LLM = mudar LLM_PROVIDER (fake | ollama). Nenhuma chave no código."""

    llm_provider: str = "fake"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    llm_timeout_s: float = 20.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "fake"),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            llm_timeout_s=float(os.getenv("LLM_TIMEOUT_S", "20")),
        )
