"""Adaptadores de IA. Único lugar do projeto que conhece um provedor de LLM."""
import httpx

from src.domain.errors import AssistantUnavailable
from src.domain.models import Stop, StopStatus
from src.infra.config import Settings

_LABEL = {
    StopStatus.OPERATING: "operando normalmente",
    StopStatus.DELAYED: "com atrasos",
    StopStatus.SUSPENDED: "suspenso",
}


class TemplateAssistant:
    """Fake documentado: resposta determinística a partir dos dados, sem LLM."""

    def answer(self, question: str, stop: Stop, alternative: Stop | None) -> str:
        text = f"O ponto {stop.name} (linhas {', '.join(stop.lines)}) está {_LABEL[stop.status]}."
        if stop.status is not StopStatus.OPERATING and alternative is not None:
            text += f" Alternativa: {alternative.name} ({alternative.id})."
        if stop.note:
            text += f" Aviso: {stop.note}."
        return text


class OllamaAssistant:
    def __init__(self, base_url: str, model: str, timeout_s: float):
        self._url = base_url.rstrip("/") + "/api/generate"
        self._model = model
        self._timeout = timeout_s

    def answer(self, question: str, stop: Stop, alternative: Stop | None) -> str:
        alt = f"{alternative.name} ({alternative.id})" if alternative else "nenhuma"
        prompt = (
            "Você é o assistente de mobilidade da prefeitura. Responda em português, em até "
            "3 frases, usando SOMENTE os dados abaixo. Se a pergunta não puder ser respondida "
            "com eles, diga que não sabe. Nunca cite dados pessoais.\n"
            f"DADOS: ponto={stop.name}; linhas={', '.join(stop.lines)}; "
            f"status={stop.status.value}; alternativa={alt}; aviso={stop.note or 'nenhum'}\n"
            f"PERGUNTA: {question}"
        )
        try:
            resp = httpx.post(
                self._url,
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return str(resp.json()["response"]).strip()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise AssistantUnavailable(str(exc)) from exc


def make_assistant(settings: Settings):
    if settings.llm_provider == "ollama":
        return OllamaAssistant(settings.ollama_url, settings.ollama_model, settings.llm_timeout_s)
    if settings.llm_provider == "fake":
        return TemplateAssistant()
    raise ValueError(f"LLM_PROVIDER inválido: {settings.llm_provider}")
