from socket import AF_INET

import aiohttp
import motor.motor_asyncio
from cryptography.fernet import Fernet

from config import config

MONGO_URL = config.get("mongo", "connection_string")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.modboty


encryption_key = config.get("mongo", "encryption_key")
fernet = Fernet(encryption_key.encode())


SIZE_POOL_AIOHTTP = 100


class SingletonAiohttp:
    session: aiohttp.ClientSession | None = None

    @classmethod
    def get_async_session(cls) -> aiohttp.ClientSession:
        if cls.session is None:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(
                family=AF_INET, limit_per_host=SIZE_POOL_AIOHTTP
            )
            cls.session = aiohttp.ClientSession(
                timeout=timeout, connector=connector
            )

        return cls.session

    @classmethod
    async def close_async_session(cls) -> None:
        if cls.session:
            await cls.session.close()
            cls.session = None
