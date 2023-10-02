from fastapi import APIRouter
from fastapi_cache.decorator import cache

from db import db
from home_page.schemas import Streamer, ChannelsData

router = APIRouter()


@router.get("/channels", response_model=ChannelsData)
@cache(expire=600)
async def get_total_channels():
    config = await db.config.find_one({"_id": 1})
    return {"channelCount": len(config["channels"]), "topChannels": config["top_streamers"]}
