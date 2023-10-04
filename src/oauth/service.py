import json
from urllib.parse import urlencode

import jwt
from aiohttp import ClientSession
from beanie.operators import Or
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from fastapi.requests import Request
from fastapi_users import models
from fastapi_users.authentication import Strategy
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.router import ErrorCode

from config import config
from oauth.base_config import auth_backend
from oauth.manager import UserManager
from oauth.models import Editors
from oauth.schemas import Body

claims = {
    "id_token": {
        "email": None,
        "email_verified": None,
        "picture": None,
        "preferred_username": None,
    }
}
claims = json.dumps(claims)

login_scope = " ".join(["user:read:email", "openid"])
authorization_scope = " ".join(
    [
        "channel:manage:broadcast",
        "channel:manage:polls",
        "channel:manage:predictions",
        "channel:manage:vips",
        "channel:read:polls",
        "channel:read:predictions",
        "channel:read:subscriptions",
        "channel:read:vips",
        "moderation:read",
        "user:read:email",
        "openid"
    ]
)

client_id = config["twitch"]["client_id"]
client_secret = config["twitch"]["client_secret"]


def get_oauth_url(intent: str, state: str) -> str:
    scope = login_scope if intent == "login" else authorization_scope
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": f"{config['app']['redirect_url']}/oauth/twitch/callback",
        "scope": scope,
        "claims": claims,
        "state": state,
    }
    return f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}"


jwks_client = jwt.PyJWKClient("https://id.twitch.tv/oauth2/keys")


async def verify_twitch_jwt(jwt_token: str) -> dict | None:
    header = jwt.get_unverified_header(jwt_token)
    key = jwks_client.get_signing_key(header["kid"]).key
    return jwt.decode(jwt_token, key, [header["alg"]], audience=client_id)


async def verify_request(request: Request, body: Body, session: ClientSession) -> tuple[dict, dict]:
    try:
        body_state, code = body.state, body.code
        cookie_state = request.cookies.get("state")
        if not cookie_state:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state cookie")

        if cookie_state != body_state:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State mismatch")

        url = "https://id.twitch.tv/oauth2/token"
        redirect_uri = f"{config['app']['redirect_url']}/oauth/twitch/callback"

        async with session.post(
            f"{url}?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={redirect_uri}"
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=response.status,
                    detail="Authorization request failed",
                )

            results = await response.json()

        twitch_jwt = results["id_token"]
        decoded_jwt = await verify_twitch_jwt(twitch_jwt)
        if decoded_jwt is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID token validation failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return results, decoded_jwt


async def process_login(
    request: Request,
    body: Body,
    user_manager: UserManager,
    strategy: Strategy[models.UP, models.ID],
    session: ClientSession,
) -> Response:
    results, decoded_jws = await verify_request(request, body, session)

    if not decoded_jws["email_verified"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unverified email")

    user = await process_oauth_callback(user_manager, results, decoded_jws, request)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    response = await auth_backend.login(strategy, user)
    await user_manager.on_after_login(user, request, response)

    return response


async def process_oauth_callback(
    user_manager: UserManager, results: dict, decoded_jws: dict, request: Request
) -> models.UOAP:
    subject_id = int(decoded_jws["sub"])

    filters = Or(Editors.channel_id == subject_id, Editors.editors == subject_id)  # type: ignore
    documents = await Editors.find(filters).to_list()

    editors = next((document.editors for document in documents if document.channel_id == subject_id), None)
    editors = list(map(str, editors))

    editor_of = [document.channel_id for document in documents if subject_id in document.editors]
    editor_of = list(map(str, editor_of))

    try:
        user = await user_manager.oauth_callback(
            "twitch",
            results["access_token"],
            decoded_jws["sub"],
            decoded_jws["email"],
            results["expires_in"],
            results["refresh_token"],
            request,
            associate_by_email=True,
            is_verified_by_default=True,
            editors=editors,
            editor_of=editor_of,
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.OAUTH_USER_ALREADY_EXISTS,
        )

    return user
