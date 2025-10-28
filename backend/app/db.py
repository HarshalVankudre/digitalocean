from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client: AsyncIOMotorClient | None = None

async def get_db():
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DB]
