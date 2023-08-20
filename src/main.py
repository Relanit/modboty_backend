from fastapi import FastAPI
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache import FastAPICache
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from auth.route import router as auth_router
from home_page.route import router as home_page_router
from database import SingletonAiohttp
from config import config


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    SingletonAiohttp.get_async_session()
    redis = aioredis.from_url(config["redis"]["redis_connection_string"], encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


@app.on_event("shutdown")
async def shutdown_event():
    await SingletonAiohttp.close_async_session()


app.include_router(auth_router)
app.include_router(home_page_router)

origins = ["http://localhost:8080", "https://modbot.xyz", "http://localhost:5000"]

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
