"""Composition root: único ponto que escolhe as implementações concretas."""
import logging

from fastapi import FastAPI

from src.api.app import create_app
from src.domain.services import AskService, StopService
from src.infra.assistants import make_assistant
from src.infra.config import Settings
from src.infra.repository import InMemoryStopRepository
from src.infra.seed import SEED_STOPS


def build_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    repo = InMemoryStopRepository(SEED_STOPS)
    assistant = make_assistant(Settings.from_env())
    return create_app(StopService(repo), AskService(repo, assistant))


app = build_app()
