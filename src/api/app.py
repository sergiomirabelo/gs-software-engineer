import logging
import time

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.schemas import AskRequest, AskResponse, Health, StopOut, StopPage
from src.domain.errors import AssistantUnavailable, InvalidQuestion, StopNotFound
from src.domain.models import StopStatus
from src.domain.services import AskService, StopService

logger = logging.getLogger("citizentech.api")

_CODES = {400: "BAD_REQUEST", 404: "NOT_FOUND", 422: "UNPROCESSABLE_ENTITY",
          503: "SERVICE_UNAVAILABLE"}


def _error(status: int, message: str, details: list[str] | None = None) -> JSONResponse:
    body = {"code": _CODES.get(status, "BAD_REQUEST"), "message": message,
            "details": details or []}
    return JSONResponse(status_code=status, content=body)


def create_app(stops: StopService, asker: AskService) -> FastAPI:
    app = FastAPI(title="CitizenTech Mobilidade API", version="1.0.0")
    app.state.stops = stops
    app.state.asker = asker

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        logger.info("http method=%s path=%s status=%s latency_ms=%.1f", request.method,
                    request.url.path, response.status_code,
                    (time.perf_counter() - started) * 1000)
        return response

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        errors = exc.errors()
        details = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in errors]
        in_body = any(e["loc"] and e["loc"][0] == "body" for e in errors)
        if in_body:
            return _error(422, "Corpo da requisição inválido", details)
        return _error(400, "Parâmetro inválido", details)

    @app.exception_handler(StopNotFound)
    async def _not_found(_: Request, exc: StopNotFound):
        return _error(404, str(exc))

    @app.exception_handler(InvalidQuestion)
    async def _invalid_question(_: Request, exc: InvalidQuestion):
        return _error(422, str(exc))

    @app.exception_handler(AssistantUnavailable)
    async def _unavailable(_: Request, exc: AssistantUnavailable):
        return _error(503, "Assistente de IA indisponível no momento. Tente novamente.")

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        return _error(exc.status_code, str(exc.detail))

    @app.get("/health", response_model=Health, operation_id="getHealth")
    def health() -> Health:
        return Health(status="ok")

    @app.get("/stops", response_model=StopPage, operation_id="listStops")
    def list_stops(
        request: Request,
        status: StopStatus | None = None,
        limit: int = Query(10, ge=1, le=50),
        offset: int = Query(0, ge=0),
    ) -> StopPage:
        items, total = request.app.state.stops.list(status=status, limit=limit, offset=offset)
        nxt = offset + limit if offset + limit < total else None
        return StopPage(items=[StopOut.from_domain(s) for s in items], total=total,
                        limit=limit, offset=offset, next_offset=nxt)

    @app.get("/stops/{stop_id}", response_model=StopOut, operation_id="getStop")
    def get_stop(stop_id: str, request: Request) -> StopOut:
        return StopOut.from_domain(request.app.state.stops.get(stop_id))

    @app.post("/ask", response_model=AskResponse, operation_id="askAssistant")
    def ask(body: AskRequest, request: Request) -> AskResponse:
        answer = request.app.state.asker.ask(body.question, body.stop_id)
        return AskResponse(answer=answer.text, stop_id=answer.stop_id, refused=answer.refused)

    return app
