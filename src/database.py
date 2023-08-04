import motor.motor_asyncio
from cryptography.fernet import Fernet

from src.config import config

mongo_connection_string = config.get("db", "mongo_connection_string")
db = motor.motor_asyncio.AsyncIOMotorClient(mongo_connection_string).modboty

encryption_key = config.get("db", "encryption_key")
fernet = Fernet(encryption_key.encode()) if encryption_key else None