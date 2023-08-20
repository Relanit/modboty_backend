from pydantic import BaseModel


class Streamer(BaseModel):
    name: str
    profile_image: str
    followers: int


class ChannelsData(BaseModel):
    channelCount: int
    topChannels: list[Streamer]
