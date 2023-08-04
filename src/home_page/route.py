from fastapi import APIRouter
from fastapi_cache.decorator import cache

from src.home_page.schemas import Streamer
from src.database import db

router = APIRouter()

@router.get("/top_streamers", response_model=list[Streamer])
@cache(expire=600)
async def get_top_streamers():
    config = await db.config.find_one({"_id": 1})
    return config["top_streamers"]


@router.get("/total_channels", response_model=int)
@cache(expire=600)
async def get_total_channels():
    config = await db.config.find_one({"_id": 1})
    return len(config["channels"])