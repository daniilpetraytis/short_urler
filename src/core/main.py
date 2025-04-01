from fastapi import FastAPI
from contextlib import asynccontextmanager

from core import events
from core.router import initialize_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await events.startup_event_handler()
    yield
    await events.shutdown_event_handler()


app = FastAPI(lifespan=lifespan)


@app.get("/ping", response_model=str)
async def read_root() -> str:
    return "pong!"


initialize_routes(app)
