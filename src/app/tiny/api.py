from aioredis import Redis

from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse, Response

from app.tiny.schemas import ShortenUrlRequest, ShortenUrlResponse, StatsResponse
from app.tiny.controllers import tiny_controller

from services.db import get_session
from services.redis import get_redis

tiny_router = APIRouter(
    tags=["Tiny"],
    prefix="",
)

stat_router = APIRouter(
    tags=["Stats"],
    prefix="",
)


@tiny_router.post(
    "/shorten",
    response_model=ShortenUrlResponse,
    status_code=status.HTTP_201_CREATED,
)
async def shorten(
    data: ShortenUrlRequest,
    db: AsyncSession = Depends(get_session),
    responses={
        status.HTTP_226_IM_USED: {"description": "Shortened url in use"},
    },
):
    return await tiny_controller.shorten(
        db=db,
        payload=data,
    )


@tiny_router.get(
    "/{short_url}",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Shortened url, not found | expired | deactivated."
        },
    },
)
async def redirect_to_main_url(
    short_url: str,
    db: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    return await tiny_controller.redirect_to_main_url(
        db=db,
        redis=redis,
        short_url=short_url,
    )


@tiny_router.get(
    "/search/{main_url:path}",
    response_model=ShortenUrlResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Shortened url, not found | expired | deactivated."
        },
    },
)
async def search_url(
    main_url: str,
    db: AsyncSession = Depends(get_session),
):
    return await tiny_controller.search_url(
        db=db,
        main_url=main_url,
    )


@stat_router.get(
    "/stats/{short_url}",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Shortened url, not found | expired | deactivated."
        },
    },
)
async def stats(
    short_url: str,
    db: AsyncSession = Depends(get_session),
):
    return await tiny_controller.get_stats(
        db=db,
        short_url=short_url,
    )


@tiny_router.delete(
    "/{short_url}",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Shortened url, not found | expired | deactivated."
        },
    },
)
async def delete_short_url(
    short_url: str,
    db=Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    return await tiny_controller.delete(
        db=db,
        redis=redis,
        short_url=short_url,
    )


@tiny_router.put(
    "/{short_url}",
    response_model=ShortenUrlResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Shortened url, not found | expired | deactivated."
        },
    },
)
async def put_short_url(
    short_url: str,
    db=Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    return await tiny_controller.put(
        db=db,
        redis=redis,
        short_url=short_url,
    )
