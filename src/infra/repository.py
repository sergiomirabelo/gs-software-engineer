import unicodedata

from src.domain.models import Stop, StopStatus


def _norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


class InMemoryStopRepository:
    def __init__(self, stops: list[Stop]):
        self._stops = {s.id: s for s in stops}

    def get(self, stop_id: str) -> Stop | None:
        return self._stops.get(stop_id)

    def list(
        self, *, status: StopStatus | None, limit: int, offset: int
    ) -> tuple[list[Stop], int]:
        items = sorted(self._stops.values(), key=lambda s: s.id)
        if status is not None:
            items = [s for s in items if s.status == status]
        return items[offset : offset + limit], len(items)

    def find_in_text(self, text: str) -> Stop | None:
        needle = _norm(text)
        for stop in self._stops.values():
            if stop.id in needle or _norm(stop.name) in needle:
                return stop
        return None
