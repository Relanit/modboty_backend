from socket import AF_INET

import aiohttp
import motor.motor_asyncio
from cryptography.fernet import Fernet

from config import config

mongo_connection_string = config.get("db", "mongo_connection_string")
db = motor.motor_asyncio.AsyncIOMotorClient(mongo_connection_string).modboty

encryption_key = config.get("db", "encryption_key")
fernet = Fernet(encryption_key.encode())


SIZE_POOL_AIOHTTP = 100


class SingletonAiohttp:
    async_session: aiohttp.ClientSession | None = None

    @classmethod
    def get_async_session(cls) -> aiohttp.ClientSession:
        if cls.async_session is None:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(
                family=AF_INET, limit_per_host=SIZE_POOL_AIOHTTP
            )
            cls.async_session = aiohttp.ClientSession(
                timeout=timeout, connector=connector
            )

        return cls.async_session

    @classmethod
    async def close_async_session(cls) -> None:
        if cls.async_session:
            await cls.async_session.close()
            cls.async_session = None
