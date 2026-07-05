from __future__ import annotations
from typing import Any, cast
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.schemas.document_schema import DocumentCreate, DocumentResponse
from app.services.pdf_processor import PDFProcessorService
from app.services.llm_provider import LLMProviderService
from app.services.vector_storage import VectorStorageService
from app.repositories.document_repository import DocumentRepository
from app.core.logger import get_logger

logger = get_logger(__name__)

router: APIRouter = APIRouter()

pdf_service: PDFProcessorService = PDFProcessorService()
llm_service: LLMProviderService = LLMProviderService()
vector_service: VectorStorageService = VectorStorageService()
repository: DocumentRepository = DocumentRepository()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a study document (PDF) with multimodal RAG analysis.",
)
async def upload_document(
    file: UploadFile = File(...), collection_name: str = Form(..., min_length=3)
) -> Any:
    """
    Ingests an uploaded PDF file, extracts its structural text content,
    processes embedded imagery using Gemini's cloud vision intelligence,
    and indexes the unified knowledge base inside ChromaDB and MongoDB.
    """
    logger.info(
        f"Received file upload request: '{file.filename}' for collection '{collection_name}'"
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

        raw_pages: Any = pdf_service.extract_text_and_images(file_bytes)
        structured_pages: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_pages)

        compiled_chunks: list[str] = []

        for page_data in structured_pages:
            page_text: str = str(page_data.get("text_content", ""))
            if page_text.strip():
                chunks: Any = pdf_service.chunk_text(page_text)
                compiled_chunks.extend(cast(list[str], chunks))

            # Corrige o nome da variável não utilizada e tipa os elementos explicitamente
            raw_images: Any = page_data.get("images", [])
            images_list: list[bytes] = cast(list[bytes], raw_images)

            for img_bytes in images_list:
                try:
                    image_description: str = (
                        await llm_service.describe_image_with_gemini(img_bytes)
                    )
                    if image_description.strip():
                        logger.info(
                            f"Injecting AI image description chunk from page {page_data.get('page_index')}."
                        )
                        img_chunks: Any = pdf_service.chunk_text(image_description)
                        compiled_chunks.extend(cast(list[str], img_chunks))
                except Exception as img_err:
                    logger.error(
                        f"Non-fatal image transcription failure on page {page_data.get('page_index')}: {str(img_err)}"
                    )
                    continue

        if not compiled_chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The supplied document does not contain any indexable text content or readable figures.",
            )

        logger.info(f"Indexing {len(compiled_chunks)} total chunks into ChromaDB...")
        # Chamada envelopada de forma segura para aceitar a execução dinâmica
        cast(Any, vector_service).store_chunks(
            collection_name=collection_name, chunks=compiled_chunks
        )

        document_payload: DocumentCreate = DocumentCreate(
            filename=filename,
            content_type=file.content_type,
            file_size_bytes=file_size,
            collection_name=collection_name,
        )

        created_record: dict[str, Any] = await repository.create(
            document_in=document_payload, total_chunks=len(compiled_chunks)
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
