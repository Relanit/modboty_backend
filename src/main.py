from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from beanie import init_beanie

from db import db, SingletonAiohttp
from oauth.schemas import UserRead, UserUpdate, UserCreate
from config import config
from home_page.route import router as home_page_router
from oauth.route import router as oauth_router
from oauth.models import User, Editors
from oauth.base_config import auth_backend, fastapi_users

app_configs = {}
if not config["app"]["show_docs"]:
    app_configs["openapi_url"] = None

app = FastAPI(**app_configs)


app.include_router(home_page_router)
app.include_router(oauth_router)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate, UserCreate),
    prefix="/users",
    tags=["users"],
)

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


@app.on_event("startup")
async def startup_event():
    SingletonAiohttp.get_async_session()
    redis = aioredis.from_url(config["redis"]["connection_string"], encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    await init_beanie(
        database=db,
        document_models=[
            User,
            Editors
        ],
    )


@app.on_event("shutdown")
async def shutdown_event():
    await SingletonAiohttp.close_async_session()
