from pydantic import BaseModel, Field

from src.domain.models import Stop, StopStatus


class StopOut(BaseModel):
    id: str
    name: str
    lines: list[str]
    status: StopStatus
    alternative_stop_id: str | None
    note: str | None

    @classmethod
    def from_domain(cls, s: Stop) -> "StopOut":
        return cls(
            id=s.id, name=s.name, lines=list(s.lines), status=s.status,
            alternative_stop_id=s.alternative_stop_id, note=s.note,
        )


class StopPage(BaseModel):
    items: list[StopOut]
    total: int
    limit: int
    offset: int
    next_offset: int | None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    stop_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    stop_id: str | None
    refused: bool


class Health(BaseModel):
    status: str
