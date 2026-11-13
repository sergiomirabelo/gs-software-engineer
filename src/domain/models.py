"""Entidades do domínio. Sem dependência de framework web nem de LLM."""
from dataclasses import dataclass
from enum import Enum


class StopStatus(str, Enum):
    OPERATING = "OPERATING"
    DELAYED = "DELAYED"
    SUSPENDED = "SUSPENDED"


@dataclass(frozen=True)
class Stop:
    id: str
    name: str
    lines: tuple[str, ...]
    status: StopStatus
    alternative_stop_id: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Answer:
    text: str
    stop_id: str | None
    refused: bool
