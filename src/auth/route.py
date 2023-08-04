import time

from fastapi import APIRouter
from fastapi.logger import logger

from src.config import config
from src.database import fernet, db
from src.singleton_aiohttp import SingletonAiohttp

router = APIRouter()

scopes = {
    "channel:manage:broadcast",
    "channel:manage:polls",
    "channel:manage:predictions",
    "channel:manage:vips",
    "channel:read:polls",
    "channel:read:predictions",
    "channel:read:subscriptions",
    "channel:read:vips",
    "moderation:read",
}


@router.post("/auth", response_model=str)
async def authorize(code: str, scope: str):
    if set(scope.split()) != scopes:
        return "3"

    client = SingletonAiohttp.get_aiohttp_client()

    try:
        async with client.post(
            f'https://id.twitch.tv/oauth2/token?client_id={config["twitch"]["client_id"]}&client_secret={config["twitch"]["client_secret"]}&code={code}&grant_type=authorization_code&redirect_uri=http://localhost:5000/auth'
        ) as response:
            if response.status != 200:
                logger.error(f"ERROR OCCURED: {str(await response.text())}")
                return "2"

            token_data = await response.json()

        if "access_token" not in token_data:
            return "2"

        async with client.get(
            "https://api.twitch.tv/helix/users",
            headers={
                "Authorization": f'Bearer {token_data["access_token"]}',
                "Client-Id": config["twitch"]["client_id"],
            },
        ) as response:
            if response.status != 200:
                logger.error(f"ERROR OCCURED: {str(await response.text())}")
                return "2"

            user_data = await response.json()
    except Exception as e:
        logger.error(f"ERROR OCCURED: {str(await response.text())}")
        return "2"

    user_id = int(user_data["data"][0]["id"])
    to_send = {
        "id": user_id,
        "access_token": fernet.encrypt(token_data["access_token"].encode()).decode(),
        "refresh_token": fernet.encrypt(token_data["refresh_token"].encode()).decode(),
        "expire_time": time.time() + token_data["expires_in"],
    }

    data = await db.config.find_one({"_id": 1})
    if user_id not in list(data["channels"]):
        return "4"

    if [
        user for user in data.get("user_tokens", [{}]) if user.get("id", "") == user_id
    ]:
        await db.config.update_one(
            {"_id": 1, "user_tokens.id": user_id},
            {"$set": {"user_tokens.$": to_send}},
        )
    else:
        await db.config.update_one({"_id": 1}, {"$addToSet": {"user_tokens": to_send}})

    return "1"
