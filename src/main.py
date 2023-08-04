import uvicorn
from fastapi import FastAPI
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache import FastAPICache
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from auth.route import router as auth_router
from home_page.route import router as home_page_router
from singleton_aiohttp import SingletonAiohttp


async def on_start_up() -> None:
    SingletonAiohttp.get_aiohttp_client()
    redis = aioredis.from_url(
        "redis://localhost", encoding="utf8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


async def on_shutdown() -> None:
    await SingletonAiohttp.close_aiohttp_client()


app = FastAPI(docs_url="/", on_startup=[on_start_up], on_shutdown=[on_shutdown])

origins = ["http://localhost:8080", "https://modbot.xyz"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=[
        "Content-Type",
        "Set-Cookie",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Authorization",
    ],
)

app.include_router(auth_router)
app.include_router(home_page_router)


# if __name__ == "__main__":  # local dev
#     uvicorn.run(app, host="localhost", port=5000)
