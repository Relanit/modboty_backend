from datetime import datetime

from beanie import PydanticObjectId
from fastapi_users import schemas
from pydantic import BaseModel


class Body(BaseModel):
    state: str
    code: str


class OAuthURL(BaseModel):
    authorization_url: str


class UserRead(schemas.BaseUser[PydanticObjectId]):
    created_at: datetime
    avatar_url: str
    account_id: str
    username: str
    display_name: str
    editors: list[str]
    editor_of: list[str]


class UserUpdate(schemas.BaseUserUpdate):
    pass
