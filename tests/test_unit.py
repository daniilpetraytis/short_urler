import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlmodel import SQLModel
from fastapi import HTTPException, status
from aioredis import Redis
from app.tiny.schemas import ShortenUrlRequest, ShortenUrlResponse, StatsResponse
from app.tiny.models import ShortenedUrl
from app.tiny.controllers import TinyController

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db

@pytest.fixture
def mock_redis():
    return AsyncMock(spec=Redis)

@pytest.mark.asyncio
async def test_shorten_generate_alias(mock_db):
    controller = TinyController()
    payload = ShortenUrlRequest(main_url="http://example.com")
    
    with patch.object(controller, 'get_stats', side_effect=HTTPException(status_code=404)) as mock_get:
        response = await controller.shorten(mock_db, payload)
        
        assert len(response.short_url) == 5
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_shorten_custom_alias_conflict(mock_db):
    controller = TinyController()
    payload = ShortenUrlRequest(main_url="http://example.com", alias="custom")

    with patch.object(controller, 'get_stats', return_value=None):
        with pytest.raises(HTTPException) as exc:
            await controller.shorten(mock_db, payload)
            
        assert exc.value.status_code == status.HTTP_226_IM_USED

@pytest.mark.asyncio
async def test_shorten_success_with_custom_alias(mock_db):
    controller = TinyController()
    payload = ShortenUrlRequest(main_url="http://example.com", alias="valid")

    with patch.object(controller, 'get_stats', side_effect=HTTPException(status_code=404)):
        response = await controller.shorten(mock_db, payload)
        
        assert response.short_url == "valid"
        mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_get_stats_not_found(mock_db):
    controller = TinyController()
    mock_db.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        await controller.get_stats(mock_db, "missing")
        
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_stats_success(mock_db):
    controller = TinyController()
    mock_url = ShortenedUrl(
        short_url="abc123",
        visits=5,
        last_usage=datetime.timestamp(datetime.utcnow()),
        expired=False,
        created_at=datetime.utcnow()
    )
    mock_db.exec.return_value.first.return_value = mock_url

    response = await controller.get_stats(mock_db, "abc123")
    
    assert response.visits == 5
    assert response.expired is False

@pytest.mark.asyncio
async def test_redirect_success(mock_db, mock_redis):
    controller = TinyController()
    mock_url = ShortenedUrl(
        short_url="test123",
        main_url="http://example.com",
        visits=0,
        last_usage=datetime.timestamp(datetime.utcnow() - timedelta(days=1)),
        expires_at=datetime.timestamp(datetime.utcnow() + timedelta(days=1)),
        expired=False,
        active=True
    )
    mock_db.exec.return_value.first.return_value = mock_url

    result = await controller.redirect_to_main_url(mock_db, mock_redis, "test123")
    
    assert result == "http://example.com"
    assert mock_url.visits == 1
    mock_db.add.assert_called_once_with(mock_url)
    mock_redis.set.assert_awaited_with("test123", "http://example.com", ex=120)

@pytest.mark.asyncio
async def test_redirect_expired(mock_db, mock_redis):
    controller = TinyController()
    mock_url = ShortenedUrl(
        short_url="expired",
        expires_at=datetime.timestamp(datetime.utcnow() - timedelta(days=1)),
        expired=False,
        active=True
    )
    mock_db.exec.return_value.first.return_value = mock_url

    with pytest.raises(HTTPException) as exc:
        await controller.redirect_to_main_url(mock_db, mock_redis, "expired")
        
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert mock_url.expired is True

@pytest.mark.asyncio
async def test_delete_success(mock_db, mock_redis):
    controller = TinyController()
    mock_url = ShortenedUrl(short_url="todelete")
    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_url))))

    response = await controller.delete(mock_db, mock_redis, "todelete")
    
    mock_db.delete.assert_awaited_once_with(mock_url)
    mock_redis.delete.assert_awaited_with("todelete")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_put_rotate_url(mock_db, mock_redis):
    controller = TinyController()
    original_url = "http://original.com"
    mock_url = ShortenedUrl(short_url="old123", main_url=original_url)
    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_url))))
    
    with patch.object(controller, 'generate_random_characters', return_value="new456"):
        response = await controller.put(mock_db, mock_redis, "old123")
        
        assert response.short_url == "new456"
        assert mock_url.short_url == "new456"
        mock_redis.delete.assert_awaited_with("old123")
        mock_redis.set.assert_awaited_with("new456", original_url, ex=120)

@pytest.mark.asyncio
async def test_search_url_found(mock_db):
    controller = TinyController()
    mock_url = ShortenedUrl(main_url="http://searched.com", short_url="found123")
    mock_db.exec.return_value.first.return_value = mock_url

    response = await controller.search_url(mock_db, "http://searched.com")
    
    assert response.short_url == "found123"

@pytest.mark.asyncio
async def test_search_url_not_found(mock_db):
    controller = TinyController()
    mock_db.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        await controller.search_url(mock_db, "http://missing.com")
        
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
