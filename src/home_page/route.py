from fastapi import APIRouter
from fastapi_cache.decorator import cache

from home_page.models import Config
from home_page.schemas import ChannelsData

router = APIRouter(tags=["Home"])


@router.get("/channels", response_model=ChannelsData)
@cache(expire=600)
async def channels():
    config = await Config.find_one(Config.id == 1)
    return {"channelCount": len(config.channels), "topChannels": config.top_streamers}
