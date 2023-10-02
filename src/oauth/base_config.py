from beanie import PydanticObjectId
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend

from config import config
from oauth.manager import get_user_manager
from oauth.models import User

cookie_transport = CookieTransport(cookie_name="modboty-token", cookie_max_age=60 * 60 * 24 * 30)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=config["app"]["secret"], lifetime_seconds=60 * 60 * 24 * 30, token_audience=["modboty-api"]
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, PydanticObjectId](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
