from pydantic import BaseModel

from datetime import datetime


class ShortenUrlRequest(BaseModel):
    main_url: str
    alias: str
    expires_at: datetime


class ShortenUrlResponse(BaseModel):
    main_url: str
    short_url: str


class StatsResponse(BaseModel):
    visits: int
    last_usage: datetime
    expired: bool
    created_at: datetime
