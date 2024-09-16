import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from home_page.models import Config, Streamer, UserToken
from main import app


@pytest.fixture(autouse=True, scope="function")
async def test_app():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    test_db = client["test_db"]

    await init_beanie(database=test_db, document_models=[Config])

    FastAPICache.init(InMemoryBackend())

    await Config.delete_all()

    yield app

    await Config.delete_all()
    client.close()


@pytest.mark.anyio
async def test_get_channels(test_app):
    config = Config(
        id=1,
        access_token="sample_access_token",
        refresh_token="sample_refresh_token",
        user_tokens=[
            UserToken(
                id=1, access_token="token1", refresh_token="refresh1", expire_time=3600
            )
        ],
        channels=[1, 2],
        top_streamers=[
            Streamer(name="streamer1", profile_image="image1.jpg", followers=1000),
            Streamer(name="streamer2", profile_image="image2.jpg", followers=2000),
        ],
        version=1,
    )
    await config.insert()

    async with AsyncClient(transport=ASGITransport(app=app)) as ac:
        response = await ac.get("http://test/channels")

    assert response.status_code == 200
    data = response.json()

    assert data["channelCount"] == 2
    expected_streamers = [
        {"name": "streamer1", "profile_image": "image1.jpg", "followers": 1000},
        {"name": "streamer2", "profile_image": "image2.jpg", "followers": 2000},
    ]
    assert data["topChannels"] == expected_streamers
