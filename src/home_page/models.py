from beanie import Document
from pydantic import BaseModel, Field


class UserToken(BaseModel):
    id: int
    access_token: str
    refresh_token: str
    expire_time: float


class Streamer(BaseModel):
    name: str
    profile_image: str
    followers: int


class Config(Document):
    id: int = Field(default_factory=int)
    access_token: str
    refresh_token: str
    user_tokens: list[UserToken] = []
    channels: list[int]
    top_streamers: list[Streamer]
    version: int

    class Settings:
        name = "config"
