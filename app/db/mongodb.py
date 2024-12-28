from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

    @classmethod
    async def connect_to_database(cls):
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.database = cls.client[settings.DB_NAME]

    @classmethod
    async def close_database_connection(cls):
        cls.client.close()

    @classmethod
    async def get_user_by_email(cls, email: str):
        return await cls.database.users.find_one({"email": email})
