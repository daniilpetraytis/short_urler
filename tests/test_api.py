import pytest
import httpx
from fastapi import status

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_shorten_url():
    payload = {
        "main_url": "https://example.com",
        "alias": "",
        "expires_at": "2025-03-31T12:00:00"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/shorten", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "short_url" in data

@pytest.mark.asyncio
async def test_shorten_duplicate_url():
    async with httpx.AsyncClient() as client:
        payload = {
            "main_url": "https://example.com",
            "alias": "",
            "expires_at": "2025-03-31T12:00:00"
        }   
        await client.post(f"{BASE_URL}/shorten", json=payload)
        response = await client.post(f"{BASE_URL}/shorten", json=payload)
        assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.asyncio
async def test_redirect():
    async with httpx.AsyncClient() as client:
        payload = {
            "main_url": "https://example.com",
            "alias": "",
            "expires_at": "2025-03-31T12:00:00"
        }  
        post_response = await client.post(f"{BASE_URL}/shorten", json=payload)
        short_url = post_response.json()["short_url"]
        response = await client.get(f"{BASE_URL}/{short_url}", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "https://example.com"

@pytest.mark.asyncio
async def test_search_url():
    async with httpx.AsyncClient() as client:
        payload = {
            "main_url": "https://example.com",
            "alias": "",
            "expires_at": "2025-03-31T12:00:00"
        }  
        await client.post(f"{BASE_URL}/shorten", json=payload)
        response = await client.get(f"{BASE_URL}/search/https://example.com")
        assert response.status_code == status.HTTP_200_OK
        assert "short_url" in response.json()

@pytest.mark.asyncio
async def test_stats():
    async with httpx.AsyncClient() as client:
        payload = {
            "main_url": "https://example.com",
            "alias": "",
            "expires_at": "2025-03-31T12:00:00"
        }  
        post_response = await client.post(f"{BASE_URL}/shorten", json=payload)
        short_url = post_response.json()["short_url"]
        response = await client.get(f"{BASE_URL}/stats/{short_url}")
        assert response.status_code == status.HTTP_200_OK
        assert "clicks" in response.json()

@pytest.mark.asyncio
async def test_delete_url():
    async with httpx.AsyncClient() as client:
        payload = {
            "main_url": "https://example.com",
            "alias": "",
            "expires_at": "2025-03-31T12:00:00"
        }  
        post_response = await client.post(f"{BASE_URL}/shorten", json=payload)
        short_url = post_response.json()["short_url"]
        response = await client.delete(f"{BASE_URL}/{short_url}")
        assert response.status_code == status.HTTP_200_OK

        response = await client.get(f"{BASE_URL}/{short_url}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_invalid_url():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/shorten", json={"url": "invalid_url"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
