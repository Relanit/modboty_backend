from datetime import datetime

from beanie import PydanticObjectId
from fastapi_users import schemas
from pydantic import BaseModel, Field

from oauth.models import OAuthAccount


class Body(BaseModel):
    state: str
    code: str


class OAuthURL(BaseModel):
    authorization_url: str


class UserRead(schemas.BaseUser[PydanticObjectId]):
    created_at: datetime
    avatar_url: str
    username: str
    display_name: str
    connections: list[OAuthAccount] = Field(default_factory=list)


class UserUpdate(schemas.BaseUserUpdate):
    pass
