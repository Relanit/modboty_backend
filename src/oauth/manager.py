from datetime import datetime

from beanie import PydanticObjectId
from fastapi import Depends
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi_users import BaseUserManager, models, exceptions
from fastapi_users_db_beanie import ObjectIDIDMixin

from oauth.models import User
from oauth.user_database import UserDatabase, get_user_db


class UserManager(ObjectIDIDMixin, BaseUserManager[User, PydanticObjectId]):
    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_login(
        self,
        user: models.UP,
        request: Request | None = None,
        response: Response | None = None,
    ) -> None:
        print(f"User {user.id} has been logged in")

    async def oauth_callback(
        self: "BaseUserManager[models.UOAP, models.ID]",
        platform: str,
        _: str,
        account_id: str,
        account_email: str,
        __: int | None = None,
        ___: str | None = None,
        request: Request | None = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
        editors=None,
        editor_of=None,
        avatar_url=None,
        username=None,
        display_name=None,
    ) -> models.UOAP:
        """
        Handle the callback after a successful OAuth authentication.

        If the user already exists with this OAuth account, the token is updated.

        If a user with the same e-mail already exists and `associate_by_email` is True,
        the OAuth account is associated to this user.
        Otherwise, the `UserNotExists` exception is raised.

        If the user does not exist, it is created and the on_after_register handler
        is triggered.
        :param platform: Name of the OAuth client.
        :param _: Valid access token for the service provider.
        :param account_id: models.ID of the user on the service provider.
        :param account_email: E-mail of the user on the service provider.
        :param __: Optional timestamp at which the access token expires.
        :param ___: Optional refresh token to get a
        fresh access token from the service provider.
        :param request: Optional FastAPI request that
        triggered the operation, defaults to None
        :param associate_by_email: If True, any existing user with the same
        e-mail address will be associated to this user. Defaults to False.
        :param is_verified_by_default: If True, the `is_verified` flag will be
        set to `True` on newly created user. Make sure the OAuth Provider you're
        using does verify the email address before enabling this flag.
        Defaults to False.
        :param editors: list of channel editors account ids
        :param editor_of: list of account ids where user is editor
        :param avatar_url: url to user's avatar
        :param display_name: user name
        :param display_name: user's display name
        :return: A user.
        """
        if editor_of is None:
            editor_of = []
        if editors is None:
            editors = []
        oauth_account_dict = {
            "platform": platform,
            "account_id": account_id,
            "account_email": account_email,
            "username": username,
            "display_name": display_name,
            "editors": editors,
            "editor_of": editor_of,
        }

        try:
            user = await self.get_by_oauth_account(platform, account_id)
        except exceptions.UserNotExists:
            try:
                # Associate account
                user = await self.get_by_email(account_email)
                if not associate_by_email:
                    raise exceptions.UserAlreadyExists()
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
            except exceptions.UserNotExists:
                # Create account
                now = datetime.utcnow()
                user_dict = {
                    "email": account_email,
                    "is_verified": is_verified_by_default,
                    "avatar_url": avatar_url,
                    "username": username,
                    "display_name": display_name,
                    "created_at": now
                }
                user = await self.user_db.create(user_dict)
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
                await self.on_after_register(user, request)
        else:
            # Update oauth
            for existing_oauth_account in user.connections:
                if (
                    existing_oauth_account.account_id == account_id
                    and existing_oauth_account.platform == platform
                ):
                    user = await self.user_db.update_oauth_account(
                        user, existing_oauth_account, oauth_account_dict
                    )

        return user


async def get_user_manager(user_db: UserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)
