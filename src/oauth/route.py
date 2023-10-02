import secrets

from fastapi import APIRouter, HTTPException, Depends
from fastapi import Response, Request, status
from fastapi_users import models
from fastapi_users.authentication import Strategy

from config import config
from oauth.base_config import get_jwt_strategy
from oauth.manager import get_user_manager, UserManager
from oauth.schemas import Body
from oauth.service import claims, login_scope, process_login

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/url")
def oauth_url(response: Response):
    url = "https://id.twitch.tv/oauth2/authorize"
    client_id = config["twitch"]["client_id"]
    redirect_uri = "http://localhost:8080/oauth/twitch/callback"
    state = secrets.token_hex(20)
    response.set_cookie(key="state", value=state, max_age=300, httponly=True, samesite="strict", secure=True)

    url = f"{url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={login_scope}&claims={claims}&state={state}"
    return {"authorization_url": url}


@router.post("/login")
async def login(
    request: Request,
    body: Body,
    user_manager: UserManager = Depends(get_user_manager),
    strategy: Strategy[models.UP, models.ID] = Depends(get_jwt_strategy),
):
    try:
        response = await process_login(request, body, user_manager, strategy)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.delete_cookie("state")
    return response


# @router.post("/oauth/authorize")
# async def authorize(
#     request: Request,
#     body: Body,
#     session: ClientSession = Depends(SingletonAiohttp.get_async_session),
# ):
#     # if set(scope.split()) != extra_scope:
#     #     raise HTTPException(
#     #         status_code=500,
#     #         detail={"status": "error", "error_code": 1, "details": None},
#     #     )
#
#     try:
#         async with session.post(
#             f'https://id.twitch.tv/oauth2/token?client_id={config["twitch"]["client_id"]}&client_secret={config["twitch"]["client_secret"]}&code={code}&grant_type=authorization_code&redirect_uri=http://localhost:5000/auth'
#         ) as response:
#             if response.status != 200:
#                 raise HTTPException(
#                     status_code=500,
#                     detail={
#                         "status": "error",
#                         "error_code": 1,
#                         "details": await response.text(),
#                     },
#                 )
#
#             token_data = await response.json()
#
#         if "access_token" not in token_data:
#             raise HTTPException(
#                 status_code=500,
#                 detail={
#                     "status": "error",
#                     "error_code": 1,
#                     "details": await response.text(),
#                 },
#             )
#
#         async with session.get(
#             "https://api.twitch.tv/helix/users",
#             headers={
#                 "Authorization": f'Bearer {token_data["access_token"]}',
#                 "Client-Id": config["twitch"]["client_id"],
#             },
#         ) as response:
#             if response.status != 200:
#                 raise HTTPException(
#                     status_code=500,
#                     detail={
#                         "status": "error",
#                         "error_code": 1,
#                         "details": await response.text(),
#                     },
#                 )
#
#             user_data = await response.json()
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={"status": "error", "error_code": 1, "details": str(e)},
#         )
#
#     user_id = int(user_data["data"][0]["id"])
#     to_send = {
#         "id": user_id,
#         "access_token": fernet.encrypt(token_data["access_token"].encode()).decode(),
#         "refresh_token": fernet.encrypt(token_data["refresh_token"].encode()).decode(),
#         "expire_time": time.time() + token_data["expires_in"],
#     }
#
#     data = await db.config.find_one({"_id": 1})
#     if user_id not in list(data["channels"]):
#         raise HTTPException(
#             status_code=500,
#             detail={"status": "error", "error_code": 2, "details": None},
#         )
#
#     if [user for user in data.get("user_tokens", [{}]) if user.get("id", "") == user_id]:
#         await db.config.update_one(
#             {"_id": 1, "user_tokens.id": user_id},
#             {"$set": {"user_tokens.$": to_send}},
#         )
#     else:
#         await db.config.update_one({"_id": 1}, {"$addToSet": {"user_tokens": to_send}})
#
#     return {"status": "success"}
