from __future__ import annotations
from typing import Any, cast
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.schemas.document_schema import DocumentCreate, DocumentResponse
from app.services.pdf_processor import PDFProcessorService
from app.services.vector_storage import VectorStorageService
from app.repositories.document_repository import DocumentRepository
from app.core.logger import get_logger
import re
import unicodedata

logger = get_logger(__name__)

router: APIRouter = APIRouter()

# Inicialização das dependências de infraestrutura locais
pdf_service: PDFProcessorService = PDFProcessorService()
vector_service: VectorStorageService = VectorStorageService()
repository: DocumentRepository = DocumentRepository()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a study document (PDF) using 100% local RAG infrastructure.",
)
async def upload_document(
    file: UploadFile = File(...), collection_name: str = Form(..., min_length=3)
) -> Any:
    """
    Ingests an uploaded PDF file, extracts its structural text content,
    and indexes the unified knowledge base inside ChromaDB and MongoDB.
    """
    logger.info(
        f"Received local file upload request: '{file.filename}' for collection '{collection_name}'"
    )

    # SANITIZAÇÃO COMPATÍVEL COM CHROMADB
    # 1. Remove acentos (transforma 'Análise' em 'Analise'
    normalized = (
        unicodedata.normalize("NFKD", collection_name)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )

    sanitized_collection = re.sub(r"[^a-zA-Z0-9._-]", "", normalized.replace(" ", "_"))

    logger.info(
        f"Sanitized collection name from '{collection_name}' to '{sanitized_collection}'"
    )

    if not file.content_type or file.content_type != "application/pdf":
        logger.warning(f"Rejected illegal file type extension: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid asset format. Only standard PDF files ('application/pdf') are supported.",
        )

    try:
        file_bytes: bytes = await file.read()
        file_size: int = len(file_bytes)
        filename: str = file.filename or "nameless_document.pdf"

        # Extração e segmentação de páginas
        raw_pages: Any = pdf_service.extract_text_and_images(file_bytes)
        structured_pages: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_pages)

        compiled_chunks: list[str] = []

        for page_data in structured_pages:
            page_text: str = str(page_data.get("text_content", ""))
            if page_text.strip():
                chunks: Any = pdf_service.chunk_text(page_text)
                compiled_chunks.extend(cast(list[str], chunks))

        if not compiled_chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The supplied document does not contain any indexable text content.",
            )

        # PASSO 1: Criação do metadado estruturado no MongoDB
        # 1. Cria o registro diretamente no MongoDB (Retorna estritamente um dict)
        document_payload: DocumentCreate = DocumentCreate(
            filename=filename,
            content_type=file.content_type,
            file_size_bytes=file_size,
            collection_name=collection_name,
        )

        created_record: dict[str, Any] = await repository.create(
            document_in=document_payload, total_chunks=len(compiled_chunks)
        )

        # 2. Extração direta do ID do dicionário (Sem ifs ou isinstance)
        id_do_documento: str = str(created_record["_id"])

        # 3. Indexação vetorial no ChromaDB local usando a nova variável
        logger.info(
            f"Indexing {len(compiled_chunks)} total chunks into local ChromaDB..."
        )
        cast(Any, vector_service).add_chunks(
            collection_name=sanitized_collection,
            chunks=compiled_chunks,
            document_id=id_do_documento,
        )

        return created_record

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            f"Fatal error executing pipeline for file '{file.filename}': {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal document ingestion failure: {str(e)}",
        )
    finally:
        await file.close()
