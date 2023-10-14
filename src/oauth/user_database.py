from typing import Dict, Any

from fastapi_users.models import OAP
from fastapi_users_db_beanie import BeanieUserDatabase, UP_BEANIE

from oauth.models import User, OAuthAccount


class UserDatabase(BeanieUserDatabase):
    async def get_by_oauth_account(self, _: str, account_id: str) -> UP_BEANIE | None:
        """Get a single user by OAuth account id."""
        if self.oauth_account_model is None:
            raise NotImplementedError()

        return await self.user_model.find_one(
            {
                "account_id": account_id,
            }
        )

    async def add_oauth_account(self, user: UP_BEANIE, create_dict: Dict[str, Any]) -> UP_BEANIE:
        """Create an OAuth account and add it to the user."""
        if self.oauth_account_model is None:
            raise NotImplementedError()

        platform = self.oauth_account_model(**create_dict)
        user.connections.append(platform)  # type: ignore

        await user.save()
        return user

    # async def update_oauth_account(
    #     self, user: UP_BEANIE, oauth_account: OAP, update_dict: Dict[str, Any]
    # ) -> UP_BEANIE:
    #     """Update an OAuth account on a user."""
    #     if self.oauth_account_model is None:
    #         raise NotImplementedError()
    #
    #     for i, existing_oauth_account in enumerate(user.connections):  # type: ignore
    #         if (
    #             existing_oauth_account.platform == oauth_account.platform
    #             and existing_oauth_account.account_id == oauth_account.account_id
    #         ):
    #             for key, value in update_dict.items():
    #                 setattr(user.connections[i], key, value)  # type: ignore
    #
    #     await user.save()
    #     return user


async def get_user_db():
    yield UserDatabase(User, OAuthAccount)
