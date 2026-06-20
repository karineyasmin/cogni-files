import io
from typing import Any
from pypdf import PageObject, PdfReader
from app.core import get_logger


logger = get_logger(__name__)


class PDFProcessorService:
    """
    Service responsible for handling document ingestion, text extraction (including OCR/Multimodal
    image processing), and chunking strategies for study materials.
    """

    @staticmethod
    def extract_text_and_images(file_bytes: bytes) -> list[dict[str, Any]]:
        """
        Reads binary bytes of a PDF file, extracts readable text, and isolates embedded images.
        Returns a list of dictionaries containing page content structured for the RAG pipeline.
        """
        logger.info(
            "Starting structural extraction (Text + Images) from uploaded PDF..."
        )
        try:
            pdf_stream: io.BytesIO = io.BytesIO(file_bytes)
            reader: PdfReader = PdfReader(pdf_stream)

            structured_pages: list[dict[str, Any]] = []

            page_number: int
            page: PageObject

            for page_number, page in enumerate(reader.pages):
                page_text: str = page.extract_text() or ""
                page_images_bytes: list[bytes] = []

                if page.images:
                    for image_file_object in page.images:
                        image_bytes: bytes = image_file_object.data
                        page_images_bytes.append(image_bytes)

                structured_pages.append(
                    {
                        "page_index": page_number + 1,
                        "text_content": page_text,
                        "images": page_images_bytes,
                    }
                )

            logger.info(
                f"Successfully processed {len(reader.pages)} pages. Found images in document."
            )
            return structured_pages

        except Exception as e:
            logger.error(f"Failed structural extraction from PDF: {str(e)}")
            raise e

    @staticmethod
    def chunck_text(
        text: str, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> list[str]:
        """
        Splits a large string of texto into smaller. overlapping slices (chunks).
        Essential for the RAG process to fit texts within LLM context windows.
        """
        logger.info(
            f"Splitting texto into chunks (Size: {chunk_size}, Overlap: {chunk_overlap})...)"
        )

        chunks: list[str] = []
        start: int = 0
        text_length: int = len(text)

        while start < text_length:
            end: int = start + chunk_size
            chunk: str = text[start:end]
            chunks.append(chunk.strip())
            start += chunk_size - chunk_overlap

        logger.info(f"Generated {len(chunks)} total chunks from document.")
        return chunks
