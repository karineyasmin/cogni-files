import chromadb
from typing import Any, cast
from app.core import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class VectorStorageService:
    """
    Service responsible for managing the Vector Database (ChromaDB),
    storing text chunks, and performing semantic search retrieval.
    """

    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        logger.info(
            f"ChromaDB initialized at storage directory: {settings.CHROMA_PERSIST_DIR}"
        )

    def get_or_create_collection(self, collection_name: str) -> Any:
        """
        Retrieves an existing vector collection or creates a new one if it does not exist.
        """
        logger.info(f"Retrieving or creating ChromaDB collection: '{collection_name}'")
        try:
            collection: Any = self.client.get_or_create_collection(name=collection_name)
            return collection

        except Exception as e:
            logger.error(f"Failed to handle collection '{collection_name}': {str(e)}")
            raise e

    def add_chunks(
        self, collection_name: str, chunks: list[str], document_id: str
    ) -> None:
        """
        Stores text chunks into the specified collection with their semantic metadata.
        """
        logger.info(f"Adding {len(chunks)} chunks to collection '{collection_name}'...")
        try:
            collection: Any = self.get_or_create_collection(collection_name)

            ids: list[str] = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

            metadatas: list[dict[str, Any]] = [
                {"document_id": document_id} for _ in chunks
            ]
            collection.add(documents=chunks, ids=ids, metadatas=metadatas)

            logger.info("Successfully indexed all chunks into Vector Storage.")
        except Exception as e:
            logger.error(f"Failed to add chunks to vector storage: {str(e)}")
            raise e

    def query_similar_chunks(
        self, collection_name: str, query_text: str, n_results: int = 3
    ) -> list[str]:
        """
        Queries the vector database for the top 'n' most semantically similar text chunks.
        """
        logger.info(
            f"Searching for top {n_results} chunks similar to query in '{collection_name}'..."
        )
        try:
            collection: Any = self.get_or_create_collection(collection_name)

            results = collection.query(query_texts=[query_text], n_results=n_results)

            retrieved_chunks: list[str] = []

            if results and "documents" in results and results["documents"]:
                documents_list: Any = results["documents"]
                if documents_list and documents_list[0]:
                    safe_list: list[Any] = cast(list[Any], documents_list[0])
                    retrieved_chunks = [str(item) for item in safe_list]

            logger.info(
                f"Successfully retrieved {len(retrieved_chunks)} relevant chunks."
            )
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Vector search query failed: {str(e)}")
            raise e
