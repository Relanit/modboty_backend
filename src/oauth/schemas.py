from beanie import PydanticObjectId
from fastapi_users import schemas
from fastapi_users.schemas import CreateUpdateDictModel
from pydantic import BaseModel


class Body(BaseModel):
    state: str
    code: str


class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass


class UserCreate(CreateUpdateDictModel):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
