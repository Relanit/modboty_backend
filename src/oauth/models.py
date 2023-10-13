from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel
from pymongo import IndexModel
from pymongo.collation import Collation


class OAuthAccount(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    platform: str
    account_id: str
    account_email: str
    username: str
    display_name: str


class User(Document):
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime
    avatar_url: str
    username: str
    display_name: str
    editors: list[str] = Field(default_factory=list)
    editor_of: list[str] = Field(default_factory=list)
    account_id: str

    class Settings:
        name = "User"
        email_collation = Collation("en", strength=2)
        indexes = [
            IndexModel("email", unique=True),
            IndexModel(
                "email", name="case_insensitive_email_index", collation=email_collation
            ),
        ]


class Editors(Document):
    channel_id: int
    channel: str | None = None
    editors: list[int]
    editor_commands: list[str] | None = None

    class Settings:
        name = "editors"
        indexes = [IndexModel("channel_id", unique=True)]
