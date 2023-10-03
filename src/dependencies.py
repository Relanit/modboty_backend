from fastapi import Depends, HTTPException, status

from oauth.base_config import fastapi_users
from oauth.models import User

current_user = fastapi_users.current_user()


async def current_user_editor(broadcaster_id: str, user: User = Depends(current_user)):
    twitch = user.platforms[0]
    if twitch.account_id == broadcaster_id:
        return user

    if broadcaster_id not in twitch.editor_of:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No editor role on the specified channel")

    return user
