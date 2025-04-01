from fastapi import FastAPI, APIRouter

from app.tiny.api import tiny_router, stat_router

main_router = APIRouter()


def initialize_routes(app: FastAPI):
    app.include_router(main_router)
    app.include_router(tiny_router)
    app.include_router(stat_router)
