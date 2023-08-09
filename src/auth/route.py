import time

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, HTTPException

from config import config
from database import fernet, db, SingletonAiohttp

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


@router.post("/auth")
async def authorize(
    code: str,
    scope: str,
    session: ClientSession = Depends(SingletonAiohttp.get_async_session),
):
    if set(scope.split()) != scopes:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "error_code": 1, "details": None},
        )

    try:
        async with session.post(
            f'https://id.twitch.tv/oauth2/token?client_id={config["twitch"]["client_id"]}&client_secret={config["twitch"]["client_secret"]}&code={code}&grant_type=authorization_code&redirect_uri=https://api.modbot.xyz/auth'
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "error_code": 1,
                        "details": await response.text(),
                    },
                )

            token_data = await response.json()

        if "access_token" not in token_data:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "error_code": 1,
                    "details": await response.text(),
                },
            )

        async with session.get(
            "https://api.twitch.tv/helix/users",
            headers={
                "Authorization": f'Bearer {token_data["access_token"]}',
                "Client-Id": config["twitch"]["client_id"],
            },
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "error_code": 1,
                        "details": await response.text(),
                    },
                )

            user_data = await response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "error_code": 1, "details": str(e)},
        )

    user_id = int(user_data["data"][0]["id"])
    to_send = {
        "id": user_id,
        "access_token": fernet.encrypt(token_data["access_token"].encode()).decode(),
        "refresh_token": fernet.encrypt(token_data["refresh_token"].encode()).decode(),
        "expire_time": time.time() + token_data["expires_in"],
    }

    data = await db.config.find_one({"_id": 1})
    if user_id not in list(data["channels"]):
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "error_code": 2, "details": None},
        )

    if [
        user for user in data.get("user_tokens", [{}]) if user.get("id", "") == user_id
    ]:
        await db.config.update_one(
            {"_id": 1, "user_tokens.id": user_id},
            {"$set": {"user_tokens.$": to_send}},
        )
    else:
        await db.config.update_one({"_id": 1}, {"$addToSet": {"user_tokens": to_send}})

    return {"status": "success"}
