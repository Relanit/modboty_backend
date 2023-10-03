from beanie import PydanticObjectId
from fastapi_users import schemas
from pydantic import BaseModel


class Body(BaseModel):
    state: str
    code: str


class AuthorizationURL(BaseModel):
    authorization_url: str


class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
