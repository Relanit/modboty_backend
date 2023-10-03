import secrets
import time

from aiohttp import ClientSession
from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from fastapi_users import models
from fastapi_users.authentication import Strategy

from db import SingletonAiohttp, fernet
from home_page.models import Config, UserToken
from oauth.base_config import get_jwt_strategy
from oauth.manager import get_user_manager, UserManager
from oauth.schemas import Body, AuthorizationURL
from oauth.service import claims, login_scope, process_login, client_id, authorization_scope, verify_request

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/url", response_model=AuthorizationURL)
def oauth_url(request: Request, response: Response):
    intent = request.cookies.get("intent")
    if intent is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing intent cookie")

    url = "https://id.twitch.tv/oauth2/authorize"
    redirect_uri = "http://localhost:8080/oauth/twitch/callback"
    state = secrets.token_hex(20)
    response.set_cookie(key="state", value=state, max_age=300, httponly=True, samesite="strict", secure=True)
    scope = login_scope if intent == "login" else authorization_scope

    url = f"{url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&claims={claims}&state={state}"
    return {"authorization_url": url}


@router.post("/login")
async def login(
    request: Request,
    body: Body,
    user_manager: UserManager = Depends(get_user_manager),
    strategy: Strategy[models.UP, models.ID] = Depends(get_jwt_strategy),
    session: ClientSession = Depends(SingletonAiohttp.get_async_session),
):
    try:
        response = await process_login(request, body, user_manager, strategy, session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response.delete_cookie("state")
    return response


@router.post("/authorize")
async def authorize(
    request: Request,
    body: Body,
    response: Response,
    session: ClientSession = Depends(SingletonAiohttp.get_async_session),
):
    try:
        results, decoded_jws = await verify_request(request, body, session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    user_id = int(decoded_jws["sub"])
    config = await Config.find_one(Config.id == 1)
    if user_id not in config.channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "error_code": 2, "details": "Bot is not connected to the channel"},
        )

    new_token = UserToken(
        id=user_id,
        access_token=fernet.encrypt(results["access_token"].encode()).decode(),
        refresh_token=fernet.encrypt(results["refresh_token"].encode()).decode(),
        expire_time=time.time() + results["expires_in"],
    )

    if user_token := next((token for token in config.user_tokens if token.id == user_id), None):
        config.user_tokens[config.user_tokens.index(user_token)] = new_token
    else:
        config.user_tokens.append(new_token)

    await config.save()
    response.delete_cookie("state")
    return {"status": "success"}
