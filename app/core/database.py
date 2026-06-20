from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Any, Mapping
from app.core import settings
from app.core import get_logger


logger = get_logger(__name__)


class MongoDBManager:
    """
    Manages the lifecycle of the asynchronous MongoDB client and database connections.
    Uses a Singleton-like approach within the application .
    """

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient[Mapping[str, Any]] | None = None
        self.db: AsyncIOMotorDatabase[Mapping[str, Any]] | None = None

    async def connect(self) -> None:
        """Establishes an asynchronous connection pool to the MongoDB instance"""
        logger.info(
            f"Attempting to connect to MongoDB at {settings.MONGO_URI.split('@')[-1]}..."
        )
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info(
                f"Successfully connected to MongoDB database: '{settings.MONGO_DB_NAME}'"
            )
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise e

    async def disconnect(self) -> None:
        """Gracefully closes all open connections in the MongoDB pool."""
        if self.client:
            self.client.close()
            logger.warning("MongoDB connection pool has been closed.")


db_manager = MongoDBManager()
