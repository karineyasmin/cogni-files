import base64
import httpx
from typing import Any
from google import genai  # type: ignore
from google.genai import types  # type: ignore
from app.core import settings
from app.core import get_logger

logger = get_logger(__name__)


class LLMProviderService:
    """
    Orchestrates LLM generation requests, routing between Google Gemini (cloud
    multimodal) and Ollama Llama 3.2 (local CPU)
    """

    def __init__(self) -> None:
        self.gemini_client: Any = genai.Client(api_key=settings.GEMINI_API_KEY)  # type: ignore
        self.http_client: Any = httpx.AsyncClient(
            base_url=settings.LOCAL_LLM_URL, timeout=60.0
        )

    async def describe_image_with_gemini(self, image_bytes: bytes) -> str:
        """
        Sends extracted document image bytes to Gemini to convert visual data into detailed text context.
        """
        logger.info(
            "Sending iamge bytes to Gemini to convert visual data into detailed text context.|"
        )
        try:
            base64_image: str = base64.b64encode(image_bytes).decode("utf-8")

            response: Any = self.gemini_client.models.generate_content(
                model=settings.LOCAL_MODEL_NAME,
                contents=[
                    types.Part.from_bytes(
                        data=base64.b64decode(base64_image), mime_type="image/png"
                    ),
                    settings.IMAGE_DESCRIPTION_PROMPT,
                ],
            )
            description: str = response.text or ""
            logger.info("Image description successfully generated.")
            return description

        except Exception as e:
            logger.error(f"Cloud image description failed: {str(e)}")
            raise e

    async def generate_local_response(
        self, prompt: str, system_instruction: str = ""
    ) -> str:
        """
        Queries the configured local LLM via a generic completions protocol.
        """
        logger.info(f"Querying local model '{settings.LOCAL_MODEL_NAME}'...")
        try:
            payload: dict[str, Any] = {
                "model": settings.LOCAL_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }
            response: httpx.Response = await self.http_client.post(
                "/v1/chat/completions", json=payload
            )
            respose.raise_for_status()  # type: ignore
            response_data: dict[str, Any] = response.json()
            answer: str = response_data["choices"][0]["message"]["content"]

            logger.info("Local response generated successfully.")
            return answer

        except Exception as e:
            logger.error(f"Local LLM generation failed: {str(e)}")
            raise e

    async def close(self) -> None:
        """Closes the active HTTP client connection pool gracefully."""
        await self.http_client.aclose()
