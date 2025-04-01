import random
import logging
import string

from datetime import datetime

from aioredis import Redis

from datetime import datetime
from fastapi import HTTPException, status, Response

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.tiny.schemas import ShortenUrlRequest, ShortenUrlResponse, StatsResponse
from app.tiny.models import ShortenedUrl


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class TinyController:
    @staticmethod
    def generate_random_characters(length: int) -> str:
        char_set = string.ascii_letters + string.digits
        return "".join(random.choice(char_set) for _ in range(length))

    async def shorten(self, db: AsyncSession, payload: ShortenUrlRequest) -> ShortenUrlResponse:

        already_used = False
        if payload.alias is None or payload.alias == "":
            while True:
                short_url = self.generate_random_characters(length=5)
                try:
                    await self.get_stats(db, payload.alias)
                except:
                    break
        else:
            short_url = payload.alias

            try:
                await self.get_stats(db, payload.alias)
                already_used = True
            except:
                pass

            if already_used:
                raise HTTPException(
                    status_code=status.HTTP_226_IM_USED,
                    detail="short url already in use",
                )

        shortened_url = ShortenedUrl(
            main_url=payload.main_url,
            short_url=short_url,
            visits=0,
            last_usage=datetime.timestamp(datetime.utcnow()),
        )
        if payload.expires_at != None:
            shortened_url.expires_at = datetime.timestamp(payload.expires_at)

        db.add(shortened_url)
        await db.commit()
        return ShortenUrlResponse(
            main_url=payload.main_url,
            short_url=short_url,
        )

    async def get_stats(self, db: AsyncSession, short_url: str) -> StatsResponse:
        statement = select(ShortenedUrl).where(
            ShortenedUrl.short_url == short_url,
        )
        results = await db.exec(statement)
        shortened_url: ShortenedUrl = results.first()
        if not shortened_url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="shortened url not found")

        return StatsResponse(
            visits=shortened_url.visits,
            last_usage=datetime.fromtimestamp(shortened_url.last_usage),
            expired=shortened_url.expired,
            created_at=shortened_url.created_at
        )

    async def search_url(self, db: AsyncSession, main_url: str) -> ShortenUrlResponse:
        main_url = main_url.replace("%3A", ":").replace("%2F", "/")
        logger.fatal("MAIN", main_url)
        statement = select(ShortenedUrl).where(ShortenedUrl.main_url == main_url)
        results = await db.exec(statement)
        shortened_url: ShortenedUrl = results.first()
        if not shortened_url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="shortened url not found")

        return ShortenUrlResponse(main_url=main_url, short_url=shortened_url.short_url)

    @staticmethod
    async def redirect_to_main_url(db: AsyncSession, redis: Redis, short_url: str) -> str:
        statement = select(ShortenedUrl).where(
            ShortenedUrl.short_url == short_url,
            ShortenedUrl.expired == False,
            ShortenedUrl.active == True,
        )
        results = await db.exec(statement)
        shortened_url: ShortenedUrl = results.first()
        if not shortened_url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="shortened url not found")

        if shortened_url.expires_at < datetime.timestamp(datetime.utcnow()):
            shortened_url.expired = True
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="shortened url not found")

        shortened_url.visits += 1
        shortened_url.last_usage = datetime.timestamp(datetime.utcnow())

        main_url = shortened_url.main_url

        db.add(shortened_url)
        await db.commit()
        await redis.set(name=short_url, value=main_url, ex=120)

        return main_url

    @staticmethod
    async def delete(db: AsyncSession, redis: Redis, short_url: str) -> Response:

        res = await db.execute(select(ShortenedUrl).filter_by(short_url=short_url))

        one = res.scalars().first()

        await db.delete(one)
        await db.commit()

        await redis.delete(short_url)
        return Response()

    async def put(self, db: AsyncSession, redis: Redis, short_url: str) -> ShortenUrlResponse:

        res = await db.execute(select(ShortenedUrl).filter_by(short_url=short_url))
        one = res.scalars().first()

        new_url = self.generate_random_characters(length=5)
        big_url = one.main_url
        one.short_url = new_url

        await db.commit()

        await redis.delete(short_url)
        await redis.set(name=new_url, value=big_url, ex=120)

        return ShortenUrlResponse(main_url=big_url, short_url=new_url)


tiny_controller = TinyController()
