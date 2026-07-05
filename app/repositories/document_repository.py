from __future__ import annotations
from typing import Any, Optional
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from bson import ObjectId
from app.core import settings
from app.core.logger import get_logger
from app.schemas.document_schema import DocumentCreate

logger = get_logger(__name__)


class DocumentRepository:
    """
    Handles asynchronous CRUD operations for Document metadata stored in MongoDB.
    Decouples database driver implementarion details from the business logic layer.
    """

    def __init__(self) -> None:
        # Inicializa o cliente assíncrono do Motor usando nossas configurações centrais
        self.client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(
            settings.MONGO_URI
        )
        self.db: AsyncIOMotorDatabase[dict[str, Any]] = self.client[
            settings.MONGO_DB_NAME
        ]
        # Define a coleção tipada para operações estritas
        self.collection: AsyncIOMotorCollection[dict[str, Any]] = self.db["documents"]

    async def create(
        self, document_in: DocumentCreate, total_chunks: int
    ) -> dict[str, Any]:
        """Inserts a tre document metadata record into MongoDB."""
        logger.info(f"Persisting document metadata for file: {document_in.filename}")
        try:
            # Converte o schema do Pydantic v2 em um dicionário Python primitivo
            document_dict: dict[str, Any] = document_in.model_dump()

            # Insere no MongoDB assincronamente
            result = await self.collection.insert_one(document_dict)

            # Atribui o ID gerado pelo banco ao dicionário de retorno
            document_dict["_id"] = str(result.inserted_id)
            logger.info(
                f"Document record successfully created with ID: {document_dict['_id']}"
            )
            return document_dict

        except Exception as e:
            logger.error(f"Failed to create document record in MongoDB: {str(e)}")
            raise e

    async def get_by_id(self, document_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieves a single document metadata record by its stringified Hex ObjectId.
        Returns None if the document does not exist or if the ID format is invalid.
        """
        logger.info(f"Fetching document with ID: {document_id}")
        try:
            if not ObjectId.is_valid(document_id):
                logger.warning(
                    f"Invalid MongoDB ObjectId format supplied: {document_id}"
                )
                return None

            document: Optional[dict[str, Any]] = await self.collection.find_one(
                {"_id": ObjectId(document_id)}
            )
            if document:
                # Converte o ObjectId nativo do BSON para string antes de devolver à aplicação
                document["_id"] = str(document["_id"])
            return document

        except Exception as e:
            logger.error(f"Error querying document by ID {document_id}: {str(e)}")
            raise e

    async def list_all(self) -> list[dict[str, Any]]:
        """
        Retrieves all registered document records ordered by the most recent ones.
        """
        logger.info("Retrieving all document metadata records...")
        try:
            documents: list[dict[str, Any]] = []
            # Cria um cursor assíncrono ordenando pelo ID decrescente (mais recente)
            cursor = self.collection.find().sort("_id", -1)

            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                documents.append(doc)

            logger.info(f"Successfully retrieved {len(documents)} document records.")
            return documents

        except Exception as e:
            logger.error(f"Failed to list documents from MongoDB: {str(e)}")
            raise e
